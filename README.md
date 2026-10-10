# Telegram Growth Crew

AI growth crew for a crypto Telegram channel. It finds channels to advertise in, checks them for fake subscribers, drafts messages to their admins, tracks cost per subscriber and writes crypto posts and a welcome message. It runs as a Claude skill and comes with a 3D **Agent World** dashboard. Nothing is posted or sent without the owner's approval.

## What's in here

| File / folder | For whom | What it is |
|---|---|---|
| `START-HERE.txt` | Channel owner | Read this first: install in 2 minutes, then type **start** |
| `2-GUIDE.html` | Channel owner | Full guide (open it in a browser) |
| `1-UPLOAD-TO-CLAUDE/telegram-growth-crew.zip` | Channel owner | The skill: upload it in Claude → Settings → Capabilities → Skills |
| `EXAMPLE-agent-world (test data).html` | Everyone | What the dashboard looks like, with test data |
| `3-FOR-YOUR-PROGRAMMER (optional)/` | Programmer | Option B (Claude + bot connector) and Option C (fully automatic bot) |
| `chatgpt/` | Channel owner | ChatGPT version (a custom GPT). Read `START-HERE-CHATGPT.txt` |
| `source/` | Programmer | Unzipped source: dashboard, skill, connector (B) and backend (C) |

## Quick start (owner)

1. Works on the free Claude plan. Pro or Max gives more room for big searches.
2. In Settings → Capabilities, turn on **Code execution and file creation**.
3. Under Customize → Skills, click **Upload skill** and choose `1-UPLOAD-TO-CLAUDE/telegram-growth-crew.zip`.
4. Turn on web search in the chat.
5. Open a new chat and type `start`.

## The crew

| Crew member | What it does |
|---|---|
| Scout | Finds crypto channels that sell ads, with their real numbers |
| Checker | Gives each channel a fraud score: clean, check by hand, or risky |
| Negotiator | Writes personal price requests and swap proposals. The owner sends them himself. |
| Tracker | Works out the cost per new subscriber for each ad |
| Strategist | Turns the owner's channel stats into growth experiments |
| Broadcaster | Writes posts (scam alerts, explainers, weekly recaps) and the "Welcome %username%!" message |

## Connecting the Telegram bot (optional)

| Option | What it adds | Needs |
|---|---|---|
| A | Everything above, inside Claude | Nothing extra |
| B | Claude posts through the owner's existing bot after he approves, makes an invite link per ad, counts joins and welcomes new members | Small server |
| C | A separate Telegram bot that sends drafts with Approve / Edit / Reject buttons | Server + Claude API key + TGStat API |

See the README inside each zip in `3-FOR-YOUR-PROGRAMMER (optional)/`.

## House rules

- Nothing is posted or sent without the owner's OK.
- No fake accounts, bought engagement or mass DMs.
- Paid promotions are always marked as ads.
- No buy/sell signals or financial advice.
- Bot tokens never go in this repository. Use `.env` files on the server.

## Support this project

Like the crew? You can support further development through [GitHub Sponsors](https://github.com/sponsors/sylvievvv). 💛
