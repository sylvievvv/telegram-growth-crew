# Telegram Growth Crew

AI growth crew for a crypto Telegram channel. It finds channels to advertise in, checks them for fake subscribers, drafts messages to their admins, tracks cost per subscriber and writes crypto posts and a welcome message. It runs as a Claude skill and comes with a 3D **Agent World** dashboard. Nothing is posted or sent without the owner's approval.

<p align="center"><a href="media/demo.mp4"><img src="media/demo.gif" alt="Telegram Growth Crew demo" width="800"></a></p>

<p align="center"><a href="media/demo.mp4">▶ Watch the full demo video (MP4)</a></p>

## The story: built for a real client

This project started as a **real client assignment**.

A crypto Telegram channel owner came to me with a problem every channel owner knows. In his own words:

> *"It's hard to make a channel grow. I can invest money in ads, but it's hard to find the right channels. I want AI working on ways to grow the channel: finding crypto channels to buy ads from, and talking to them."*

He didn't want another bot that spams people or buys fake followers. He wanted a **team** that works for him and only acts when he says yes.

So I built him one.

| The problem | What the crew does about it |
|---|---|
| Finding channels to advertise in takes hours | The **Scout** finds them, with real numbers |
| Many channels have fake subscribers or bought views | The **Checker** gives every channel a fraud score before you pay a cent |
| Writing to admins one by one | The **Negotiator** drafts personal price requests and swap offers |
| No idea which ads actually work | The **Tracker** works out the cost per new subscriber for every ad |
| No time to make content | The **Broadcaster** writes scam alerts, explainers and the "Welcome %username%!" message |
| Afraid of losing control | Nothing goes out without his **Approve** |

**The brief:** no programmer, no servers, no API bills, and it had to feel fun to use. That's why it runs inside his own Claude, and why his crew lives in a 3D neon city where you can watch the ninjas walk to work.

**Delivered:**
- the Claude skill;
- the 3D Agent World dashboard;
- a step-by-step guide;
- a ChatGPT version;
- two optional bot integrations for his programmer.

All of it is tested on real Telegram channels.

> 💡 **Want a crew like this for your own niche?** E-commerce, real estate, agencies, creators: the same idea works anywhere. Reach out through [GitHub](https://github.com/sylvievvv) and let's talk.

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
