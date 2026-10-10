"""Scout + Fraud Checker pipeline.

run_scout(["defi", "crypto news"]) searches TGStat, keeps channels inside the size
range, fetches their stats and subscriber history, scores them for fraud and saves
new ones as leads. Returns a short summary the bot can send to the owner.
"""
import re
from typing import Any

import db
import fraud
from config import settings
from tgstat import TGStat, TGStatError

CONTACT_RE = re.compile(r"(?<![\w.])@([A-Za-z][A-Za-z0-9_]{4,31})|t\.me/([A-Za-z][A-Za-z0-9_]{4,31})")
AD_WORDS = ("реклам", "ads", "advert", "promo", "sponsor", "publicidad", "werbung", "cooperation", "сотруднич")


def find_contacts(about: str, own_username: str) -> list[str]:
    """Admin contacts written in the channel description, ad contacts first."""
    found: list[str] = []
    own = own_username.lstrip("@").lower()
    for m in CONTACT_RE.finditer(about or ""):
        name = (m.group(1) or m.group(2)).lower()
        if name != own and name not in ("joinchat", "addlist", "share") and "@" + name not in found:
            found.append("@" + name)
    lines = (about or "").lower().splitlines()
    ad_lines = " ".join(line for line in lines if any(w in line for w in AD_WORDS))
    found.sort(key=lambda c: 0 if c[1:] in ad_lines else 1)
    return found


def run_scout(keywords: list[str], per_keyword: int = 40, api: TGStat | None = None) -> dict[str, Any]:
    api = api or TGStat()
    db.init()
    seen: dict[str, dict] = {}
    errors: list[str] = []
    for kw in keywords:
        try:
            for item in api.search(q=kw if len(kw) >= 3 else None, limit=per_keyword):
                uname = (item.get("username") or "").lower()
                if not uname or uname in seen or db.lead_exists(uname):
                    continue
                subs = int(item.get("participants_count") or 0)
                if settings.min_subscribers <= subs <= settings.max_subscribers:
                    item["_kw"] = kw
                    seen[uname] = item
        except TGStatError as e:
            errors.append(str(e))

    added, flagged = [], []
    for uname, item in seen.items():
        try:
            stat = api.stat(uname)
            history = api.subscribers(uname, days=30)
        except TGStatError as e:
            errors.append(f"{uname}: {e}")
            continue
        score, reasons = fraud.score_channel(stat, history, item.get("tgstat_restrictions"))
        lead = {
            "username": uname,
            "title": item.get("title"),
            "link": item.get("link"),
            "about": item.get("about"),
            "subscribers": stat.get("participants_count"),
            "avg_post_reach": stat.get("avg_post_reach"),
            "err_percent": stat.get("err_percent"),
            "er_percent": stat.get("er_percent"),
            "ci_index": stat.get("ci_index"),
            "language": settings.tgstat_language or None,
            "admin_contacts": find_contacts(item.get("about") or "", uname),
            "fraud_score": score,
            "fraud_reasons": reasons,
            "found_with": item["_kw"],
        }
        lead_id = db.add_lead(lead)
        lead["id"] = lead_id
        (flagged if score >= 60 else added).append(lead)

    return {"clean_or_check": added, "risky": flagged, "errors": errors}


def summary_text(result: dict[str, Any]) -> str:
    ok, bad = result["clean_or_check"], result["risky"]
    lines = [f"Scout found {len(ok) + len(bad)} new channels: {len(ok)} worth a look, {len(bad)} risky."]
    for lead in sorted(ok, key=lambda l: l["fraud_score"])[:10]:
        reach = lead.get("avg_post_reach") or 0
        lines.append(f"• {lead['username']} · {lead['subscribers']:,} subs · ~{reach:,} views · "
                     f"fraud {lead['fraud_score']} ({fraud.label(lead['fraud_score'])}) · /lead_{lead['id']}")
    if bad:
        lines.append("Risky (skipped): " + ", ".join(l["username"] for l in bad[:8]))
    if result["errors"]:
        lines.append(f"{len(result['errors'])} lookups failed (see server log).")
    return "\n".join(lines)
