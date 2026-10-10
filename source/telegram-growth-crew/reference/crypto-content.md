# Crypto content for the owner's channel

The Broadcaster writes posts for the owner's own channel. The Strategist does the research first when a post needs current facts. Every post goes to the Approval inbox (`crew.py draft ... post`). Nothing is posted until the owner says yes.

## The four post types

| Type | When | Research first? |
|---|---|---|
| Scam alert | Weekly, or when a scam is going around | Yes: web search for scams reported in the last 7–14 days |
| Explainer (one term) | 2–3 times a week | Only if the term is new or has changed recently |
| Weekly recap | Once a week (Friday or Sunday) | Yes: web search for the week's main news |
| Welcome / start here | Once, then pin it | No |

## Research (scam alerts and recaps)

1. Run 2–4 web searches, for example:
   - `crypto scam warning <this month> <year>`
   - `fake airdrop phishing <year>`
   - `crypto news this week <topic>`, or the owner's niche (DeFi, Bitcoin, Ethereum, Layer 2…)
2. Use reliable sources:
   - official project blogs and accounts;
   - regulators and police warnings;
   - security firms;
   - established crypto news sites.

   Prefer facts confirmed by two sources.
3. Keep the source links. Put them in the header above the draft for the owner, and offer "Sources in the comments" in the post.
4. If you cannot confirm something, leave it out.

## How every post looks

- In the language of the owner's channel.
- A title line with one emoji.
- Short lines and bullets. At most about 900 characters, so it reads well on a phone.
- One practical takeaway ("how to spot it", "what to check").
- It ends with a question or a call to save or share the post, which helps reach.
- Explainers and recaps add the line "Education only, not financial advice." in the channel's language.

## Never

- Price predictions, price targets, "buy", "sell", "entry", "this coin will pump", or portfolio tips.
- Shilling a token, or presenting a project as a good investment.
- Invented numbers, quotes or news. If you are unsure, leave it out.
- Naming a person or company as a scammer unless an official source says so. Describe the method instead.
- Paid posts without "#ad" or "Paid partnership".

## Save the draft

Write the post to a file, then run:
```bash
python scripts/crew.py draft growth-crew.xlsx post @hischannel @hischannel "Scam alert: fake airdrop sites" post1.txt
```
Show the post in a code block too, so he can copy it. If the connector tools are on, follow "When the Telegram Growth connector is on" in SKILL.md: preview first, then post only after a clear yes.

## Content plan (when he asks for a week of posts)

Suggest a simple week. For example:
- **Mon:** explainer
- **Wed:** scam alert
- **Thu:** poll
- **Fri:** weekly recap
- **Sun:** explainer

Draft the first two posts and save them. Also save the plan as an idea:
```bash
python scripts/crew.py idea growth-crew.xlsx "Weekly content plan" "Mon explainer, Wed scam alert, Thu poll, Fri recap, Sun explainer. Compare views per post after 2 weeks."
```
