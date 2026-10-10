# Agent World backend (Option C): fully automatic bot

> Option C of the Growth Crew: runs on its own and needs a Claude API key. For the simpler setup where the owner's own Claude does the work, see Option B (`telegram-connector.zip`). If both run, give each its own new bot token.

## Scout, Fraud Checker and Negotiator

First real part of Agent World. It does the three jobs the channel owner cares about most:

1. **Scout** finds crypto Telegram channels that could sell ads (via the TGStat API).
2. **Fraud Checker** scores every channel from 0 (clean) to 100 (fake) and says why.
3. **Negotiator** uses Claude to write one personal message per channel admin.

The owner controls everything from a private chat with a new Telegram bot, the "Agent World bot".
Nothing is ever sent to channel admins automatically. The owner approves each message and sends it himself.
That keeps outreach personal and avoids Telegram spam bans.

The existing bot that posts to the channel is not touched.

## What you need

| What | Where to get it | Goes in `.env` as |
|---|---|---|
| A new bot token | Telegram → @BotFather → `/newbot` | `TELEGRAM_BOT_TOKEN` |
| The owner's chat id | Start the bot, send `/myid` | `OWNER_CHAT_ID` |
| TGStat API token | tgstat.ru → API (a paid plan with "Stat API" access) | `TGSTAT_TOKEN` |
| Claude API key | console.anthropic.com → API keys | `ANTHROPIC_API_KEY` |

You also need Python 3.11+ and a small always-on server (any VPS works).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values
python tgstat.py categories # shows TGStat category codes: put the crypto one in TGSTAT_CATEGORY
python tgstat.py languages  # optional: language code for TGSTAT_LANGUAGE
python tgstat.py countries  # optional: country code for TGSTAT_COUNTRY
python tests/test_pipeline.py   # offline tests, no tokens needed
python bot.py
```

Run `bot.py` with systemd, pm2 or Docker so it restarts on its own.

## How the owner uses it (in Telegram)

| Command | What happens |
|---|---|
| `/scout defi, crypto news, bitcoin` | Scout searches these words, keeps channels between `MIN_SUBSCRIBERS` and `MAX_SUBSCRIBERS`, checks them for fakes and replies with the best ones |
| `/leads` | The best clean new channels, each with a `/lead_12` link |
| `/lead_12` | Numbers, fraud reasons and admin contact for one channel, plus buttons: *Draft price request*, *Draft swap*, *Negotiating*, *Booked*, *Not interested* |
| `/draftall` | The Negotiator writes messages for the 5 best clean channels (at most 5 per run, on purpose) |
| `/drafts` | Shows messages still waiting |
| `/welcome` | Shows the welcome message. `/welcome Welcome %username%! …` changes it after a preview with Save / Cancel |
| `/adlink criptonoticias_oct` | Makes an invite link for one ad. People who tap it are approved at once and get the welcome message |

Each draft comes with **Approve / Edit / Reject** buttons.
- **Approve:** the bot sends the final text as a plain message to copy, plus a link to the admin's chat. The lead becomes "contacted".
- **Edit:** the owner types a new version.

## Welcome message ("Welcome %username%!")

- **Channel:** people who join through a link made with `/adlink` get the welcome message in a private chat. The link is a "request to join" link, and the bot approves them right away.
- **Discussion group (optional):** set `WELCOME_GROUP_ID`. New members are greeted in the group by name.
- `%username%` becomes their @username, or their first name if they have none. `%firstname%` is always the first name.
- **What Telegram does not allow:** a bot cannot message people who join a public channel straight through @username. Use a pinned welcome post for them.
- **Admin rights:** the bot needs to be admin of the channel with "Invite users via link", and of the group if you use it.
- **Settings:** set `CHANNEL_ID` (defaults to `MY_CHANNEL`) and optionally `WELCOME_TEXT` in `.env`.

## How the fraud score works (`fraud.py`)

The score is built from simple rules, and every point comes with a readable reason.

| Signal | Why it matters |
|---|---|
| Views per post compared to subscribers | Real channels usually reach 8–30% of subscribers. Under 6% suggests fake subscribers; over 90% suggests bought views. |
| Views but almost no reactions or shares | Bought views rarely react. |
| One-day subscriber jumps (last 30 days) | Bought subscribers arrive all at once. |
| Big subscriber drops | Often happen when Telegram removes fake accounts. |
| TGStat's own warning marks | Scam or fake labels. |

Score labels:
- **under 30:** clean
- **30–59:** check by hand
- **60 and up:** risky (skipped)

Tune the thresholds after checking a few channels by hand.

## Files

| File | Job |
|---|---|
| `bot.py` | The Agent World bot (entry point) |
| `scout.py` | Search → filter → stats → fraud score → save |
| `fraud.py` | Fraud score and reasons |
| `negotiator.py` | Claude writes the admin messages (rules in `SYSTEM`) |
| `tgstat.py` | TGStat API client, plus helper to list category/language/country codes |
| `db.py` | SQLite: `leads` and `drafts` |
| `api.py` | Optional JSON for the dashboard (`uvicorn api:app`); put it behind a login |
| `tests/test_pipeline.py` | Offline tests with a fake TGStat |

## Costs and limits

- **TGStat requests:** each new channel costs about 2 TGStat requests (stats + subscriber history), plus 1 per search word. Check your plan's monthly limit.
- **Claude API:** each draft is one short call.
- **Ad prices:** TGStat does not know ad prices. They come from the admin's answer; fill them in on the dashboard or in the database.
- **Admin contacts:** taken from the channel description. When none is found, the owner has to look in the channel's pinned post.

## Next parts

- **Ad Tracker:** the Agent World bot creates an invite link per booked ad (`createChatInviteLink`, needs the admin right "Invite users via link"). It then counts joins per link from `chat_member` updates.
- **Growth Strategist:** reads the owner's own channel stats via TGStat and asks Claude for weekly experiments.
- **Broadcaster:** sends approved posts through the existing bot.
- **Dashboard:** serve the Agent World page from the same server and read `api.py`.
