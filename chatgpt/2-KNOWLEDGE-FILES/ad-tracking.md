# Tracking which ads work

## Before the ad goes live (owner, in the Telegram app)
1. Open the channel → Edit/Manage → Invite links → Create a new link.
2. Name the link after the channel that will post the ad, for example `ad_defiradar_oct`.
3. Give that link to the admin. Only this link goes in their post.

## A week later
In Invite links, each link shows how many people joined through it. The owner sends you, per ad:
- the channel;
- the date;
- the price paid;
- "joined".

Log each ad in the workbook with `crew ad growth-crew.xlsx @channel YYYY-MM-DD <cost> <joined>`. The "Ad log" sheet then has these columns:
`channel,date,cost_usd,joined,cost_per_subscriber,verdict,notes`

Work out the numbers like this:
- `cost_per_subscriber` = cost ÷ joined. If joined is 0, write "none joined" (never divide by 0). That ad is "avoid" straight away.
- `verdict`:
  - **rebook** = cheapest third;
  - **ok** = middle;
  - **avoid** = most expensive third, or fewer than 20 joined.

Show the ranking. Then say how much of the monthly budget is spent and how much is left.

## Tips
- Compare channels on cost per subscriber, not on price per post.
- Count again after 30 days: some subscribers leave. A channel whose people stay is worth more.
- Book the best channel again, and test one new channel every week.
