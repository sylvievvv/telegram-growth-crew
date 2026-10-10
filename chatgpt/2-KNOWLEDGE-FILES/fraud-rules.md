# Fraud rules (used by crew.py)

Score from 0 (looks clean) to 100 (almost surely fake). Each rule adds points and a plain-language reason.

| Signal | Points | Why |
|---|---|---|
| Views per post unknown (or shown as 0) | +35 | No data: check the channel by hand |
| Views per post under 2% of subscribers | +70 | Most subscribers never see posts: fake or inactive |
| Views per post 2–4% | +50 | Many subscribers probably fake or inactive |
| Views per post 4–6% | +30 | Low reach |
| Views per post 6–8% | +12 | A bit low |
| Views per post over 90% of subscribers | +25 | Views may be bought |
| ER under 0.1% while reach is normal (8%+) | +15 | Views without any reactions or shares |
| 7-day growth over 15% of subscribers | +30 | Sudden jump, typical of bought subscribers |
| 7-day growth 7–15% | +15 | Unusual jump (could also be a big ad: check by hand) |
| Signals / VIP / pump channel | +60 | Followers want trade calls; always risky for education-channel ads |
| 30-day loss over 8% of subscribers | +10 | Big drops often follow removal of fake accounts |

Verdicts:
- **under 30:** clean
- **30–59:** check by hand
- **60 and up:** risky (do not buy)

Healthy crypto channels usually reach 8–30% of subscribers per post.

Small, active channels (5k–30k) with 15%+ reach are often the cheapest subscribers. Big channels with 2% reach are usually expensive and partly fake.

The rules are a filter, not proof. Before paying, the owner should open the channel, scroll the last 20 posts and check that views look natural: not identical numbers on every post, and not views far above reactions on every post.
