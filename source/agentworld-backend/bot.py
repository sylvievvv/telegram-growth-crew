"""Agent World bot: the owner's private control panel in Telegram.

Run:  python bot.py

What the owner can do in the private chat with this bot:
  /scout defi, crypto news   find channels for these words, check them for fakes
  /leads                     best clean channels found so far
  /lead_12                   one channel: numbers, fraud reasons, buttons to draft a message
  /draftall                  draft price requests for the 5 best new clean channels
  /drafts                    messages still waiting for approval
  /welcome                   see or change the welcome message ("Welcome %username%!")
  /adlink criptonoticias_oct invite link for one ad; people who use it get the welcome message
  /myid                      shows your chat id (put it in OWNER_CHAT_ID)

Every draft arrives with Approve / Edit / Reject buttons. Approve gives you the
final text to copy and a link to the admin's chat: you send it yourself.
This bot never messages channel admins on its own.
"""
import asyncio
import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, ChatJoinRequestHandler, ChatMemberHandler,
                          CommandHandler, ContextTypes, MessageHandler, filters)

import db
import fraud
import negotiator
import welcome
from config import settings
from scout import run_scout, summary_text

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("agentworld")

OWNER = filters.Chat(chat_id=settings.owner_chat_id) if settings.owner_chat_id else filters.Chat(chat_id=[])
MAX_DRAFTS_PER_RUN = 5  # keeps outreach personal: no mass messaging


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def lead_card(lead: dict) -> str:
    reach = lead.get("avg_post_reach") or 0
    subs = lead.get("subscribers") or 0
    ratio = f"{reach / subs:.0%}" if subs else "?"
    contacts = ", ".join(lead.get("admin_contacts") or []) or "not in description: check the channel"
    reasons = "\n".join(f"  • {esc(r)}" for r in lead.get("fraud_reasons") or [])
    return (f"<b>{esc(lead['title'])}</b> ({esc(lead['username'])})\n"
            f"Subscribers: {subs:,} · views per post: ~{reach:,} ({ratio})\n"
            f"Fraud score: <b>{lead['fraud_score']}</b> ({fraud.label(lead['fraud_score'])})\n{reasons}\n"
            f"Admin: {esc(contacts)}\nStatus: {esc(lead['status'])}")


def lead_buttons(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Draft price request", callback_data=f"draft:price_request:{lead_id}"),
         InlineKeyboardButton("Draft swap", callback_data=f"draft:swap:{lead_id}")],
        [InlineKeyboardButton("Negotiating", callback_data=f"status:{lead_id}:negotiating"),
         InlineKeyboardButton("Booked", callback_data=f"status:{lead_id}:booked"),
         InlineKeyboardButton("Not interested", callback_data=f"status:{lead_id}:rejected")],
    ])


def draft_buttons(draft_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{draft_id}"),
        InlineKeyboardButton("✏️ Edit", callback_data=f"edit:{draft_id}"),
        InlineKeyboardButton("✖ Reject", callback_data=f"reject:{draft_id}"),
    ]])


async def send_draft(ctx: ContextTypes.DEFAULT_TYPE, draft_id: int) -> None:
    d = db.get_draft(draft_id)
    lead = db.get_lead(d["lead_id"])
    head = "Price request" if d["kind"] == "price_request" else "Swap proposal"
    await ctx.bot.send_message(
        settings.owner_chat_id,
        f"<b>{head}</b> for {esc(lead['username'])} → {esc(d['to_contact'] or 'admin unknown')}\n\n{esc(d['text'])}",
        parse_mode="HTML", reply_markup=draft_buttons(draft_id))


async def make_draft(ctx: ContextTypes.DEFAULT_TYPE, lead_id: int, kind: str) -> None:
    lead = db.get_lead(lead_id)
    text = await asyncio.to_thread(negotiator.draft_message, lead, kind)
    contact = (lead.get("admin_contacts") or [None])[0]
    draft_id = db.add_draft(lead_id, kind, contact, text)
    await send_draft(ctx, draft_id)


# ---------- commands ----------
async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Your chat id: {update.effective_chat.id}")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(__doc__.split("What the owner can do", 1)[1].split("Every draft")[0].strip())


async def cmd_scout(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    raw = " ".join(ctx.args) if ctx.args else ""
    keywords = [k.strip() for k in raw.split(",") if k.strip()] or ["crypto", "defi", "bitcoin"]
    await update.message.reply_text(f"Scout is searching: {', '.join(keywords)}. This takes a minute…")
    result = await asyncio.to_thread(run_scout, keywords)
    await update.message.reply_text(summary_text(result))


async def cmd_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    leads = db.list_leads(status="new", max_fraud=59, limit=15)
    if not leads:
        await update.message.reply_text("No clean new leads yet. Try /scout defi, crypto news")
        return
    lines = [f"/lead_{l['id']} {l['username']} · {l['subscribers']:,} subs · fraud {l['fraud_score']}" for l in leads]
    await update.message.reply_text("Best new channels:\n" + "\n".join(lines))


async def cmd_lead(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    lead_id = int(update.message.text.split("_", 1)[1].split("@")[0])
    lead = db.get_lead(lead_id)
    if not lead:
        await update.message.reply_text("Lead not found.")
        return
    await update.message.reply_text(lead_card(lead), parse_mode="HTML", reply_markup=lead_buttons(lead_id))


async def cmd_draftall(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    todo = [l for l in db.list_leads(status="new", max_fraud=29, limit=30) if not db.has_open_draft(l["id"])]
    todo = todo[:MAX_DRAFTS_PER_RUN]
    if not todo:
        await update.message.reply_text("No clean leads without a draft. Run /scout first.")
        return
    await update.message.reply_text(f"Negotiator is writing {len(todo)} personal messages…")
    for lead in todo:
        await make_draft(ctx, lead["id"], "price_request")


async def cmd_drafts(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    waiting = db.list_drafts("waiting")
    if not waiting:
        await update.message.reply_text("Nothing waiting for approval.")
    for d in waiting[:10]:
        await send_draft(ctx, d["id"])


# ---------- buttons ----------
async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    action, *rest = q.data.split(":")
    if action == "welcome":
        await welcome.on_welcome_button(update, ctx, rest[0])
    elif action == "draft":
        kind, lead_id = rest[0], int(rest[1])
        await q.message.reply_text("Negotiator is writing…")
        await make_draft(ctx, lead_id, kind)
    elif action == "status":
        lead_id, status = int(rest[0]), rest[1]
        db.set_lead_status(lead_id, status)
        await q.message.reply_text(f"Status set to {status}.")
    elif action == "approve":
        d = db.get_draft(int(rest[0]))
        db.decide_draft(d["id"], "approved")
        db.set_lead_status(d["lead_id"], "contacted")
        await q.edit_message_reply_markup(None)
        contact = d["to_contact"]
        link = f"\nOpen chat: https://t.me/{contact.lstrip('@')}" if contact else ""
        await q.message.reply_text(f"Approved. Copy the text below and send it yourself.{link}")
        await q.message.reply_text(d["text"])  # plain message: easy to copy
    elif action == "reject":
        db.decide_draft(int(rest[0]), "rejected")
        await q.edit_message_reply_markup(None)
        await q.message.reply_text("Rejected. Nothing was sent.")
    elif action == "edit":
        ctx.user_data["editing"] = int(rest[0])
        await q.message.reply_text("Send me the new text for this message.")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    draft_id = ctx.user_data.pop("editing", None)
    if draft_id:
        db.update_draft_text(draft_id, update.message.text)
        await send_draft(ctx, draft_id)
    else:
        await update.message.reply_text("Use /scout, /leads, /draftall or /drafts. /help shows everything.")


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    db.init()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("myid", cmd_myid))
    if not settings.owner_chat_id:
        log.warning("OWNER_CHAT_ID is not set: only /myid works. Send /myid to the bot and put the number in .env")
    app.add_handler(CommandHandler(["start", "help"], cmd_help, filters=OWNER))
    app.add_handler(CommandHandler("scout", cmd_scout, filters=OWNER))
    app.add_handler(CommandHandler("leads", cmd_leads, filters=OWNER))
    app.add_handler(CommandHandler("draftall", cmd_draftall, filters=OWNER))
    app.add_handler(CommandHandler("drafts", cmd_drafts, filters=OWNER))
    app.add_handler(MessageHandler(OWNER & filters.Regex(r"^/lead_\d+"), cmd_lead))
    app.add_handler(CommandHandler("welcome", welcome.cmd_welcome, filters=OWNER))
    app.add_handler(CommandHandler("adlink", welcome.cmd_adlink, filters=OWNER))
    app.add_handler(ChatJoinRequestHandler(welcome.on_join_request))
    app.add_handler(ChatMemberHandler(welcome.on_group_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(OWNER & filters.TEXT & ~filters.COMMAND, on_text))
    log.info("Agent World bot is running")
    app.run_polling(allowed_updates=Update.ALL_TYPES)  # ALL_TYPES: needed for join requests and new members


if __name__ == "__main__":
    main()
