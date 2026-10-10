"""Negotiator: Claude writes one personal message per channel admin.

Drafts only. The owner approves in Telegram and sends the message himself from his
own account. Nothing here sends messages to admins.
"""
from typing import Any

import anthropic

from config import settings

SYSTEM = """You write short, personal first messages from a Telegram channel owner to the admin of another crypto Telegram channel.

Rules:
- One message, 60 to 120 words, friendly and direct. No hype, no emojis spam (at most one), no exclamation-mark chains.
- Write in the language of the other channel if it is given (for example Spanish for 'es'); otherwise English.
- Mention something specific about their channel (its topic or title) so it does not read like a template.
- Say who you are in one line: the owner's channel and what it is about.
- Clearly say that any paid post would be marked as an ad.
- Never give financial advice, price predictions or buy/sell signals.
- Never invent numbers about the owner's channel beyond what you are given.
- End with one clear question.
- Output only the message text, nothing else."""

PRICE = ("Goal: ask the price for one ad post (24 hours at the top) and whether they offer a package of 3 posts. "
         "Ask for their recent views per post if they share stats.")
SWAP = ("Goal: propose a free cross-promotion swap: each channel posts one short shout-out for the other "
        "at an agreed time, both clearly marked. Offer to share stats first.")


def _client() -> anthropic.Anthropic:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def draft_message(lead: dict[str, Any], kind: str = "price_request") -> str:
    goal = SWAP if kind == "swap" else PRICE
    about = (lead.get("about") or "")[:500]
    sign = settings.my_name or "[your name]"
    user = f"""Owner's channel: {settings.my_channel} ({settings.my_channel_pitch}). Sign as: {sign}.

Their channel: {lead.get('title')} ({lead.get('username')})
Language: {lead.get('language') or 'unknown'}
Subscribers: {lead.get('subscribers')}
Their description: {about}

{goal}"""
    msg = _client().messages.create(
        model=settings.claude_model,
        max_tokens=400,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in msg.content if block.type == "text").strip()
