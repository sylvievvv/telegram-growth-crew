TELEGRAM GROWTH CREW - READ ME FIRST
====================================

What this is
------------
An add-on ("skill") for your own Claude. It turns Claude into a small crew
that helps grow your crypto Telegram channel:

  Scout       finds crypto channels that sell ads, with their real numbers
  Checker     spots fake subscribers and bought views before you pay
  Negotiator  writes personal messages to channel admins (you send them)
  Tracker     shows which ads brought subscribers, and what each one cost
  Strategist  gives growth ideas based on your own channel stats
  Broadcaster writes crypto posts for your channel: scam alerts,
              explainers and weekly recaps (you approve before posting)

No API keys, no server, no programmer needed. It runs inside your Claude.


Install (one time, about 2 minutes)
-----------------------------------
You need a Claude Pro or Max plan.

1. Open claude.ai (or the Claude app on a computer).
2. Go to Settings > Capabilities.
   - Turn ON "Code execution and file creation".
3. In the same page, find "Skills" and click "Upload skill".
   - Choose the file in the folder 1-UPLOAD-TO-CLAUDE:
     telegram-growth-crew.zip (do not unzip that one).
   - Make sure the switch next to "telegram-growth-crew" is ON.
4. In a chat, make sure web search is turned on (the tools/search toggle
   next to the message box).

That's it.


First use
---------
Open a new chat and type:   start

Claude asks you three short questions: your channel, where you want to
advertise, and your budget. Answer in one message. Claude then saves your
answers, finds your first channels right away, and gives you two files:

  growth-crew.xlsx   your lists: setup, channels, ads, drafts, activity
  agent-world.html   your crew as 3D ninjas in a neon street, replaying what
                     they just did, with tabs for your leads, ads, inbox and
                     daily report. Open it in your browser.

Keep that file. Next time, attach growth-crew.xlsx to the chat and just say
what you want. Claude remembers everything through that file: your setup,
all channels found, and all ads you booked.

Tip: make a Claude Project called "Telegram Growth" and add growth-crew.xlsx
to the project files. Then you never have to attach it again.


Things you can ask
------------------
  Find 15 Spanish DeFi channels to advertise in
  Check @channelname for fake subscribers
  Write price requests for the 5 best clean channels
  Ad on @channel cost $60, 140 people joined via my link
  (send a screenshot of your channel statistics) -> growth ideas
  Write this week's scam alert
  Explain staking in 60 seconds
  Weekly crypto recap
  Write a welcome message: Welcome %username%!
  menu


Connect your Telegram bot? (optional)
-------------------------------------
Everything above works WITHOUT connecting your bot (option A).
Your programmer can add more later. Pick one:

  B  Claude + bot connector: Claude can post approved messages through
     your existing bot, make an invite link per ad, count the joins, and
     send "Welcome %username%!" to everyone who joins through your ad links.
     Give your programmer: option-B-telegram-connector.zip
  C  Fully automatic bot in Telegram that sends you drafts with
     Approve / Edit / Reject buttons (needs a Claude API key).
     Give your programmer: option-C-agentworld-backend.zip

Comparison table: GUIDE.html, section 8. Advice: start with A.


Safety
------
Claude never sends messages or pays anyone. It only prepares; you decide
and send. No fake accounts, no bought views, no buy/sell signals, and paid
posts are always marked as ads.

More explanation: open 2-GUIDE.html in your browser.
