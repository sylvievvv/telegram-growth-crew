"""Telegram Growth connector: lets the owner's own Claude use his Telegram bots.

Add it in Claude: Settings > Connectors > Add custom connector, URL:
    https://YOUR-DOMAIN/<CONNECTOR_SECRET>/mcp

Tools Claude gets:
    channel_overview   channel name and current subscriber count
    post_to_channel    post an approved message through the owner's EXISTING bot (two-step: preview, then confirm)
    create_ad_link     make a named invite link for one ad (via the Agent World bot)
    ad_results         joins per ad link, counted live from Telegram
    welcome_message    read or change the welcome message new members get ("Welcome %username%!")

Two bots, on purpose:
  POSTING_BOT_TOKEN   the owner's existing bot. Only used to SEND posts, so it never
                      interferes with what that bot already does.
  TRACKING_BOT_TOKEN  a NEW bot (from @BotFather), admin of the channel with the right
                      "Invite users via link". It makes the ad links and listens for joins.
                      Never use the existing bot here: two programs reading the same bot's
                      updates break each other.

Welcome message ("Welcome %username%!"):
  * Ad links are made as "request to join" links. When someone taps one, the Agent World
    bot approves them at once and sends them the welcome message in a private chat.
    (Telegram lets a bot message someone who just asked to join; it cannot message
    people who join a public channel straight through @username.)
  * Optional: set WELCOME_GROUP_ID to your discussion group. New members there are
    greeted in the group by name. The Agent World bot must be admin of that group.
"""
import asyncio
import logging
import os
import re
import sqlite3
import time

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

log = logging.getLogger("tg-connector")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

POSTING = os.getenv("POSTING_BOT_TOKEN", "")
TRACKING = os.getenv("TRACKING_BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL_ID", "")          # @channelname or -100… id
SECRET = os.getenv("CONNECTOR_SECRET", "")     # long random string, part of the URL
DB = os.getenv("DB_PATH", "connector.db")
PORT = int(os.getenv("PORT", "8080"))
WELCOME_GROUP = os.getenv("WELCOME_GROUP_ID", "")   # optional discussion group (@name or -100… id)
WELCOME_ON_LINKS = os.getenv("WELCOME_ON_AD_LINKS", "yes").lower() not in ("no", "0", "false")
DEFAULT_WELCOME = os.getenv("WELCOME_TEXT", "Welcome %username%! 👋 Glad you're here. Start with our pinned post. "
                                           "We share crypto explainers and polls: no signals, no financial advice.")

if not SECRET or len(SECRET) < 24:
    raise SystemExit("Set CONNECTOR_SECRET to a long random string (at least 24 characters)")

SIGNALS = re.compile(r"\b(buy|sell|long|short)\s+(now|signal|this)\b|price target|guaranteed|100x|to the moon", re.I)
AD_MARK = re.compile(r"#ad\b|paid partnership|publicidad|реклама|sponsored", re.I)


# ---------------- storage ----------------
def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS links (link TEXT PRIMARY KEY, name TEXT, created INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS joins (link TEXT, user_id INTEGER, at INTEGER, left_at INTEGER,
                   PRIMARY KEY (link, user_id))""")
    con.execute("""CREATE TABLE IF NOT EXISTS state (k TEXT PRIMARY KEY, v TEXT)""")
    return con


def get_welcome() -> str:
    row = db().execute("SELECT v FROM state WHERE k='welcome'").fetchone()
    return row[0] if row else DEFAULT_WELCOME


def fill_welcome(text: str, user: dict) -> str:
    """%username% -> @username (or first name if they have none), %firstname% -> first name."""
    first = (user.get("first_name") or "there").strip()
    handle = "@" + user["username"] if user.get("username") else first
    return text.replace("%username%", handle).replace("%firstname%", first)


# ---------------- Telegram ----------------
async def tg(token: str, method: str, **params):
    if not token:
        raise RuntimeError(f"Bot token for {method} is not set on the server")
    async with httpx.AsyncClient(timeout=40) as http:
        r = await http.post(f"https://api.telegram.org/bot{token}/{method}", json=params)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram said: {data.get('description', data)}")
    return data["result"]


async def greet_join_request(con, req: dict):
    """Someone tapped a 'request to join' ad link: approve, count the join, send the welcome DM."""
    user = req["from"]
    link = (req.get("invite_link") or {}).get("invite_link")
    await tg(TRACKING, "approveChatJoinRequest", chat_id=req["chat"]["id"], user_id=user["id"])
    if link:
        con.execute("INSERT OR IGNORE INTO joins (link, user_id, at) VALUES (?,?,?)", (link, user["id"], req["date"]))
    try:
        await tg(TRACKING, "sendMessage", chat_id=req.get("user_chat_id", user["id"]), text=fill_welcome(get_welcome(), user))
    except Exception as e:  # the person may have blocked bots; joining still worked
        log.info("welcome DM not delivered: %s", e)


def is_welcome_group(chat: dict) -> bool:
    if not WELCOME_GROUP:
        return False
    return str(chat.get("id")) == WELCOME_GROUP or ("@" + (chat.get("username") or "")).lower() == WELCOME_GROUP.lower()


async def handle_update(con, u: dict):
    if u.get("chat_join_request"):
        await greet_join_request(con, u["chat_join_request"])
        return
    cm = u.get("chat_member")
    if not cm:
        return
    user = cm["new_chat_member"]["user"]
    new, old = cm["new_chat_member"]["status"], cm["old_chat_member"]["status"]
    joined = new in ("member", "restricted") and old in ("left", "kicked")
    if is_welcome_group(cm.get("chat") or {}):
        if joined:
            await tg(TRACKING, "sendMessage", chat_id=cm["chat"]["id"], text=fill_welcome(get_welcome(), user))
        return
    link = (cm.get("invite_link") or {}).get("invite_link")
    if joined and link:
        con.execute("INSERT OR IGNORE INTO joins (link, user_id, at) VALUES (?,?,?)", (link, user["id"], cm["date"]))
    elif new in ("left", "kicked"):
        con.execute("UPDATE joins SET left_at=? WHERE user_id=? AND left_at IS NULL", (cm["date"], user["id"]))


async def listen_for_joins():
    """Counts who joins the channel through each ad link, and sends the welcome message."""
    if not TRACKING:
        log.warning("TRACKING_BOT_TOKEN not set: ad_results will stay empty and no welcome messages go out")
        return
    con = db()
    row = con.execute("SELECT v FROM state WHERE k='offset'").fetchone()
    offset = int(row[0]) if row else 0
    while True:
        try:
            updates = await tg(TRACKING, "getUpdates", offset=offset, timeout=30,
                               allowed_updates=["chat_member", "chat_join_request"])
        except Exception as e:  # network trouble: wait and keep listening
            log.warning("join listener: %s", e)
            await asyncio.sleep(10)
            continue
        for u in updates:
            offset = u["update_id"] + 1
            try:
                await handle_update(con, u)
            except Exception as e:  # one bad update must not stop the others
                log.warning("update %s: %s", u.get("update_id"), e)
        con.execute("INSERT OR REPLACE INTO state VALUES ('offset', ?)", (str(offset),))
        con.commit()


mcp = FastMCP(
    "Telegram Growth",
    instructions=("Tools for the owner's Telegram channel. Never post without the owner's explicit yes in this "
                  "chat. Never post buy/sell signals. Paid promotions must be marked as an ad."),
    host="0.0.0.0", port=PORT, streamable_http_path=f"/{SECRET}/mcp", stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.tool()
async def channel_overview() -> dict:
    """Channel title, @username and current subscriber count."""
    token = TRACKING or POSTING
    chat = await tg(token, "getChat", chat_id=CHANNEL)
    count = await tg(token, "getChatMemberCount", chat_id=CHANNEL)
    return {"title": chat.get("title"), "username": "@" + chat["username"] if chat.get("username") else None,
            "subscribers": count}


@mcp.tool()
async def post_to_channel(text: str, is_paid_promo: bool = False, confirmed: bool = False) -> dict:
    """Post a message to the owner's channel through his existing bot.

    Always call first with confirmed=false: you get a preview to show the owner.
    Only call again with confirmed=true after the owner clearly says yes in the chat.
    Set is_paid_promo=true for any paid or sponsored post; it must then be marked #ad.
    """
    problems = []
    if SIGNALS.search(text):
        problems.append("Reads like a buy/sell signal or profit promise: not allowed.")
    if is_paid_promo and not AD_MARK.search(text):
        problems.append("Paid promo must be marked as an ad: add '#ad' or 'Paid partnership'.")
    if len(text) > 4096:
        problems.append("Too long for one Telegram message (max 4096 characters).")
    if problems:
        return {"posted": False, "problems": problems}
    if not confirmed:
        return {"posted": False, "preview": text,
                "next": "Show this preview to the owner. Only if he says yes, call again with confirmed=true."}
    msg = await tg(POSTING, "sendMessage", chat_id=CHANNEL, text=text, disable_web_page_preview=False)
    return {"posted": True, "message_id": msg["message_id"]}


@mcp.tool()
async def create_ad_link(ad_name: str) -> dict:
    """Make a separate invite link for one ad, e.g. ad_name='ad_criptonoticias_oct'.
    Give this link to the admin of the channel that runs the ad."""
    name = re.sub(r"[^\w\-]", "_", ad_name)[:32]
    extra = {"creates_join_request": True} if WELCOME_ON_LINKS else {}
    res = await tg(TRACKING, "createChatInviteLink", chat_id=CHANNEL, name=name, **extra)
    con = db()
    con.execute("INSERT OR REPLACE INTO links VALUES (?,?,?)", (res["invite_link"], name, int(time.time())))
    con.commit()
    return {"name": name, "link": res["invite_link"],
            "note": "People who tap it are approved at once and get the welcome message." if WELCOME_ON_LINKS else ""}


@mcp.tool()
async def ad_results() -> list[dict]:
    """How many people joined through each ad link, and how many of them already left."""
    con = db()
    rows = con.execute("""SELECT l.name, l.link, l.created,
                                 COUNT(j.user_id), SUM(CASE WHEN j.left_at IS NOT NULL THEN 1 ELSE 0 END)
                          FROM links l LEFT JOIN joins j ON j.link = l.link
                          GROUP BY l.link ORDER BY l.created DESC""").fetchall()
    return [{"ad": n, "link": lk, "created": time.strftime("%Y-%m-%d", time.gmtime(c)),
             "joined": j, "left_again": lf or 0, "still_in": j - (lf or 0)} for n, lk, c, j, lf in rows]


@mcp.tool()
async def welcome_message(new_text: str = "", confirmed: bool = False) -> dict:
    """Read or change the welcome message that every new member gets.

    Use %username% for their @username (or first name if they have none) and %firstname% for the first name.
    Without new_text: returns the current message. With new_text: call first with confirmed=false to get a
    preview for the owner; only after he clearly says yes, call again with confirmed=true to save it.
    """
    example = {"first_name": "Alex", "username": "alex_crypto"}
    if not new_text:
        cur = get_welcome()
        return {"welcome_message": cur, "example": fill_welcome(cur, example),
                "sent_to": ("people who join through your ad links (private message)" if WELCOME_ON_LINKS else "nobody via ad links")
                           + (" and new members of your discussion group" if WELCOME_GROUP else "")}
    problems = []
    if SIGNALS.search(new_text):
        problems.append("Reads like a buy/sell signal or profit promise: not allowed.")
    if len(new_text) > 1000:
        problems.append("Keep the welcome message under 1000 characters.")
    if "%username%" not in new_text and "%firstname%" not in new_text:
        problems.append("Add %username% or %firstname% so each person is greeted by name.")
    if problems:
        return {"saved": False, "problems": problems}
    if not confirmed:
        return {"saved": False, "preview": fill_welcome(new_text, example),
                "next": "Show this preview to the owner. Only if he says yes, call again with confirmed=true."}
    con = db()
    con.execute("INSERT OR REPLACE INTO state VALUES ('welcome', ?)", (new_text,))
    con.commit()
    return {"saved": True, "welcome_message": new_text}


async def run():
    """Web server for Claude, plus the join/welcome listener running all the time next to it."""
    import uvicorn
    listener = asyncio.create_task(listen_for_joins())
    try:
        await uvicorn.Server(uvicorn.Config(mcp.streamable_http_app(), host="0.0.0.0", port=PORT)).serve()
    finally:
        listener.cancel()


if __name__ == "__main__":
    log.info("Connector URL path: /%s…/mcp on port %s", SECRET[:4], PORT)
    asyncio.run(run())
