"""Fraud Checker: a transparent score from 0 (looks clean) to 100 (almost surely fake).

Every point added comes with a plain-language reason, so the owner can see WHY a
channel is flagged instead of trusting a black box. Tune the thresholds after you
have checked a few channels by hand.
"""
from statistics import median
from typing import Any


def score_channel(stat: dict[str, Any], history: list[dict[str, Any]] | None = None,
                  restrictions: list | None = None) -> tuple[int, list[str]]:
    score, reasons = 0, []
    subs = int(stat.get("participants_count") or 0)
    reach = int(stat.get("avg_post_reach") or 0)
    err = stat.get("err_percent")
    er = stat.get("er_percent")

    if subs <= 0:
        return 100, ["No subscriber data"]

    # 1. Views compared to subscribers. Real crypto channels usually get 8-30% of subs per post.
    ratio = reach / subs
    if ratio < 0.03:
        score += 45; reasons.append(f"Posts reach only {ratio:.1%} of subscribers: most subscribers are probably fake")
    elif ratio < 0.06:
        score += 30; reasons.append(f"Low reach: {ratio:.1%} of subscribers see a post")
    elif ratio < 0.08:
        score += 12; reasons.append(f"Reach a bit low: {ratio:.1%} of subscribers")
    elif ratio > 0.9:
        score += 25; reasons.append(f"Reach is {ratio:.0%} of subscribers, unusually high: views may be bought")

    # 2. Views without any interaction can mean bought views.
    if er is not None and ratio >= 0.08 and float(er) < 0.1:
        score += 15; reasons.append(f"Almost no reactions or shares (ER {float(er):.2f}%) despite normal views")

    # 3. Sudden subscriber jumps (bought subscribers arrive in one or two days).
    if history and len(history) >= 7:
        counts = [int(h["participants_count"]) for h in sorted(history, key=lambda h: h["period"])]
        gains = [b - a for a, b in zip(counts, counts[1:])]
        typical = max(1.0, median(abs(g) for g in gains))
        biggest = max(gains)
        if biggest > max(10 * typical, 0.03 * subs):
            score += 30; reasons.append(f"Sudden jump of +{biggest:,} subscribers in one day (normal is about {int(typical):,})")
        elif biggest > max(5 * typical, 0.015 * subs):
            score += 15; reasons.append(f"Unusual jump of +{biggest:,} subscribers in one day")
        drops = [g for g in gains if g < -max(5 * typical, 0.01 * subs)]
        if drops:
            score += 10; reasons.append("Big subscriber drops, often seen after fake accounts get removed")

    # 4. TGStat's own warnings (scam / fake marks).
    if restrictions:
        score += 40; reasons.append(f"TGStat warning on this channel: {restrictions}")

    if err is not None and float(err) < 3:
        score += 10; reasons.append(f"Very low engagement rate (ERR {float(err):.1f}%)")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append(f"Healthy: posts reach {ratio:.0%} of subscribers")
    return score, reasons


def label(score: int) -> str:
    if score < 30:
        return "clean"
    if score < 60:
        return "check by hand"
    return "risky"
