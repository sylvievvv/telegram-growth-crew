"""Welcome message for new members: "Welcome %username%!".

How it reaches people (Telegram's rules):
  * Channel: ad links made with /adlink are "request to join" links. When someone taps one,
    this bot approves them at once and sends the welcome in a private chat.
    A bot cannot message people who join a public channel straight through @username.
  * Discussion group (optional, WELCOME_GROUP_ID): new members are greeted in the group by name.
The bot must be admin of the channel ("Invite users via link") and of the group, if used.
"""
import os
import re

from telegram import ChatMemberUpdated, Update
from telegram.ext import ContextTypes

import db
from config import settings

DEFAULT = os.getenv("WELCOME_TEXT", "Welcome %username%! 👋 Glad you're here. Start with our pinned post. "
                                    "We share crypto explainers and polls: no signals, no financial advice.")
GROUP = os.getenv("WELCOME_GROUP_ID", "")
CHANNEL = os.getenv("CHANNEL_ID", "") or settings.my_channel
SIGNALS = re.compile(r"\b(buy|sell|long|short)\s+(now|signal|this)\b|price target|guaranteed|100x|to the moon", re.I)


def get_text() -> str:
    return db.get_setting("welcome") or DEFAULT


def fill(text: str, user) -> str:
    """%username% -> @username (or first name if they have none), %firstname% -> first name."""
    first = (getattr(user, "first_name", None) or "there").strip()
    handle = "@" + user.username if getattr(user, "username", None) else first
    return text.replace("%username%", handle).replace("%firstname%", first)


def problems(text: str) -> list[str]:
    out = []
    if SIGNALS.search(text):
        out.append("Reads like a buy/sell signal or profit promise: not allowed.")
    if len(text) > 1000:
        out.append("Keep it under 1000 characters.")
    if "%username%" not in text and "%firstname%" not in text:
        out.append("Add %username% or %firstname% so each person is greeted by name.")
    return out


async def on_join_request(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    req = update.chat_join_request
    await req.approve()
    try:
        await ctx.bot.send_message(req.user_chat_id, fill(get_text(), req.from_user))
    except Exception:  # they may block bots; joining still worked
        pass


def _joined(cm: ChatMemberUpdated) -> bool:
    return cm.old_chat_member.status in ("left", "kicked") and cm.new_chat_member.status in ("member", "restricted")


async def on_group_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    cm = update.chat_member
    chat = cm.chat
    is_group = GROUP and (str(chat.id) == GROUP or ("@" + (chat.username or "")).lower() == GROUP.lower())
    if is_group and _joined(cm):
        await ctx.bot.send_message(chat.id, fill(get_text(), cm.new_chat_member.user))


async def cmd_welcome(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/welcome shows the message; /welcome <new text> shows a preview with Save / Cancel."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    new = update.message.text.partition(" ")[2].strip()
    if not new:
        cur = get_text()
        await update.message.reply_text(f"Current welcome message:\n\n{cur}\n\nExample:\n{fill(cur, _Example)}\n\n"
                                        "To change it: /welcome Welcome %username%! …")
        return
    bad = problems(new)
    if bad:
        await update.message.reply_text("Not saved:\n• " + "\n• ".join(bad))
        return
    ctx.user_data["welcome_new"] = new
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Save", callback_data="welcome:save"),
                                InlineKeyboardButton("Cancel", callback_data="welcome:cancel")]])
    await update.message.reply_text("Preview:\n\n" + fill(new, _Example), reply_markup=kb)


async def on_welcome_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
    q = update.callback_query
    await q.edit_message_reply_markup(None)
    new = ctx.user_data.pop("welcome_new", None)
    if choice == "save" and new:
        db.set_setting("welcome", new)
        await q.message.reply_text("Saved. New members get this message from now on.")
    else:
        await q.message.reply_text("Not changed.")


async def cmd_adlink(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/adlink criptonoticias_oct makes a named invite link for one ad (with the welcome message)."""
    name = re.sub(r"[^\w\-]", "_", " ".join(ctx.args) or "ad")[:32]
    link = await ctx.bot.create_chat_invite_link(CHANNEL, name=name, creates_join_request=True)
    await update.message.reply_text(f"Link for {name}:\n{link.invite_link}\n\nGive it to the admin of that channel. "
                                    "People who tap it are approved at once and get your welcome message. "
                                    "Telegram shows the joins per link under Channel → Invite links.")


class _Example:
    first_name = "Alex"
    username = "alex_crypto"
