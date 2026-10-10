"""Growth Crew workbook: one Excel file that holds everything.

The workbook (growth-crew.xlsx) has four sheets:
  Start here   what each sheet is for
  My setup     the owner's channel, targets and budget (asked once)
  Leads        every channel found, with fraud score, fair price and status
  Ad log       every booked ad with cost, joins and cost per subscriber

Commands (Claude runs these; the owner never has to):
  python scripts/crew.py setup BOOK --channel @name --topic "..." --language English \
      --targets "Spanish, English" --niches "DeFi, news" --size 5000-150000 --budget 30-120 --monthly 1000
  python scripts/crew.py add BOOK channels.csv      score new channels and add them to Leads
  python scripts/crew.py status BOOK @channel contacted [--price 80]
  python scripts/crew.py ad BOOK @channel 2026-10-12 60 140   (channel, date, cost, joined)
  python scripts/crew.py show BOOK                  print setup + summary (read this first)
  python scripts/crew.py log BOOK scout "Found 12 channels, 7 look clean"   what a crew member did
  python scripts/crew.py draft BOOK dm @channel @admin "Price request" message.txt   save a draft
  python scripts/crew.py drafted BOOK              mark all waiting drafts as handled
  python scripts/crew.py idea BOOK "Post at 19:30" "Your evening posts get 40% more views. Try 7 days."
  python scripts/crew.py dashboard BOOK agent-world.html   the visual crew page with all real data

channels.csv columns (empty = unknown):
  username,title,language,niche,subscribers,avg_views,recent_views,er_percent,
  growth_24h,growth_7d,growth_30d,admin_contact,notes,source_url
"""
import argparse
import csv
import os
import sys
from datetime import date

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:
    sys.exit("openpyxl is needed: pip install openpyxl")

LEAD_COLS = ["username", "title", "language", "niche", "subscribers", "avg_views", "recent_views", "reach_percent",
             "fair_price_usd", "fraud_score", "verdict", "reasons", "admin_contact", "status", "agreed_price",
             "er_percent", "growth_7d", "growth_30d", "notes", "source_url", "added_on"]
AD_COLS = ["channel", "date", "cost_usd", "joined", "cost_per_subscriber", "verdict", "notes"]
DRAFT_COLS = ["date", "time", "kind", "channel", "to", "title", "text", "state"]
ACT_COLS = ["date", "time", "agent", "text"]
IDEA_COLS = ["date", "idea", "details", "status"]
AGENT_KEYS = {"navigator": "nav", "nav": "nav", "scout": "scout", "checker": "fraud", "fraud": "fraud",
              "negotiator": "nego", "nego": "nego", "broadcaster": "broad", "broad": "broad",
              "strategist": "growth", "growth": "growth", "tracker": "ads", "ads": "ads",
              "treasurer": "treas", "treas": "treas"}
SETUP_KEYS = [("channel", "My channel"), ("topic", "What it is about"), ("language", "Language"),
              ("subscribers", "Subscribers"), ("targets", "Advertise in (languages/regions)"),
              ("niches", "Niches to target"), ("size", "Channel size to target"),
              ("budget", "Budget per ad (USD)"), ("monthly", "Monthly ad budget (USD)"),
              ("welcome", "Welcome message (%username% = their name)")]
STATUSES = ("new", "contacted", "negotiating", "booked", "done", "not interested")
FILL = {"clean": "D9F2E3", "check by hand": "FCEFD0", "risky": "FBE1DE",
        "rebook": "D9F2E3", "ok": "FCEFD0", "avoid": "FBE1DE"}
HEAD = PatternFill("solid", fgColor="1F3036")
WHITE = Font(bold=True, color="FFFFFF")


def num(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


# ---------------- fraud score ----------------
def score(row):
    subs, views, er = num(row.get("subscribers")), num(row.get("avg_views")), num(row.get("er_percent"))
    g7, g30 = num(row.get("growth_7d")), num(row.get("growth_30d"))
    if not subs:
        return None, 100, "risky", "No subscriber number"
    pts, why = 0, []
    reach = (views / subs) if views else None  # 0 views usually means the page had no data
    if reach is None:
        pts += 35; why.append("Views per post unknown: check the channel by hand")
    elif reach < 0.02:
        pts += 70; why.append(f"Posts reach only {reach:.1%} of subscribers: most are fake or inactive")
    elif reach < 0.04:
        pts += 50; why.append(f"Posts reach only {reach:.1%} of subscribers: many are probably fake or inactive")
    elif reach < 0.06:
        pts += 30; why.append(f"Low reach: {reach:.1%} of subscribers see a post")
    elif reach < 0.08:
        pts += 12; why.append(f"Reach a bit low: {reach:.1%}")
    elif reach > 0.9:
        pts += 25; why.append(f"Reach {reach:.0%} of subscribers is unusually high: views may be bought")
    if er is not None and reach is not None and reach >= 0.08 and er < 0.1:
        pts += 15; why.append(f"Almost no reactions (ER {er:.2f}%) despite normal views")
    if g7 is not None:
        r7 = g7 / subs
        if r7 > 0.15:
            pts += 30; why.append(f"+{int(g7):,} subscribers in 7 days ({r7:.0%}): sudden jump")
        elif r7 > 0.07:
            pts += 15; why.append(f"+{int(g7):,} subscribers in 7 days ({r7:.0%}): unusual, check if they ran ads")
    niche = (row.get("niche") or "").lower()
    if any(w in niche for w in ("signal", "pump", "vip")):
        pts += 60; why.append("Signals/VIP channel: followers want trade calls, ads rarely convert (do not buy)")
    if g30 is not None and g30 / subs < -0.08:
        pts += 10; why.append(f"Lost {int(-g30):,} subscribers in 30 days: often fake accounts being removed")
    recent = num(row.get("recent_views"))
    if recent and views and (recent > views * 2.5 or recent < views * 0.3):
        pts += 15; why.append(f"Recent posts get {int(recent):,} views vs {int(views):,} average: check by hand")
    if any(w in (row.get("notes") or "").lower() for w in ("bot", "same views", "identical", "no posts", "dead")):
        pts += 20; why.append("Red flag on the Telegram preview: " + row["notes"])
    pts = max(0, min(100, pts))
    verdict = "clean" if pts < 30 else "check by hand" if pts < 60 else "risky"
    if not why:
        why.append(f"Healthy: posts reach {reach:.0%} of subscribers")
    return reach, pts, verdict, "; ".join(why)


# ---------------- workbook ----------------
def sheet_rows(ws, cols):
    rows = []
    for vals in ws.iter_rows(min_row=2, values_only=True):
        if any(v not in (None, "") for v in vals):
            rows.append({c: ("" if v is None else v) for c, v in zip(cols, vals)})
    return rows


EXTRA = {"drafts": [], "activity": [], "ideas": []}


def load(book):
    if not os.path.exists(book):
        return {}, [], []
    wb = load_workbook(book)
    setup = {}
    if "My setup" in wb.sheetnames:
        labels = {lbl: key for key, lbl in SETUP_KEYS}
        for lbl, val in wb["My setup"].iter_rows(min_row=2, values_only=True):
            if lbl in labels:
                setup[labels[lbl]] = "" if val is None else val
    leads = sheet_rows(wb["Leads"], LEAD_COLS) if "Leads" in wb.sheetnames else []
    ads = sheet_rows(wb["Ad log"], AD_COLS) if "Ad log" in wb.sheetnames else []
    EXTRA["drafts"] = sheet_rows(wb["Drafts"], DRAFT_COLS) if "Drafts" in wb.sheetnames else []
    EXTRA["activity"] = sheet_rows(wb["Activity"], ACT_COLS) if "Activity" in wb.sheetnames else []
    EXTRA["ideas"] = sheet_rows(wb["Ideas"], IDEA_COLS) if "Ideas" in wb.sheetnames else []
    return setup, leads, ads


def table(ws, cols, rows, verdict_col, widths):
    ws.append(cols)
    for c in ws[1]:
        c.font, c.fill = WHITE, HEAD
    for r in rows:
        ws.append([r.get(k, "") for k in cols])
        f = FILL.get(r.get(verdict_col))
        if f:
            ws.cell(ws.max_row, cols.index(verdict_col) + 1).fill = PatternFill("solid", fgColor=f)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    ws.freeze_panes = "B2"


def save(book, setup, leads, ads):
    wb = Workbook()
    st = wb.active; st.title = "Start here"
    lines = [
        ("Telegram Growth Crew", ""),
        ("", ""),
        ("How to use", "Open Claude, attach this file, and say what you want. Claude reads your setup and lists from it."),
        ("Find channels", 'e.g. "Find 15 Spanish DeFi channels to advertise in"'),
        ("Check a channel", 'e.g. "Check @channelname for fake subscribers"'),
        ("Write to admins", 'e.g. "Write price requests for the 5 best clean channels"'),
        ("Track an ad", 'e.g. "Ad on @channel cost $60, 140 people joined via my link"'),
        ("Growth ideas", "Send a screenshot of your channel statistics"),
        ("", ""),
        ("My setup", "Your channel and targets. Change them here or just tell Claude."),
        ("Leads", "Channels found. Green = clean, yellow = check by hand, red = risky (do not buy)."),
        ("Ad log", "Booked ads. Green = book again, red = avoid."),
        ("Drafts / Activity / Ideas", "Messages waiting for you, what the crew did, and growth ideas."),
        ("agent-world.html", "Open it to see your crew at work with all your real data."),
        ("fair_price_usd", "A fair price for one post, from its real views at $8-20 per 1,000 views."),
        ("", ""),
        ("Rules", "Claude never sends anything itself. You approve and send every message. Ads are marked as ads."),
    ]
    for a, b in lines:
        st.append([a, b])
    st["A1"].font = Font(bold=True, size=16)
    for r in range(3, 18):
        st.cell(r, 1).font = Font(bold=True)
    st.column_dimensions["A"].width = 18
    st.column_dimensions["B"].width = 100

    su = wb.create_sheet("My setup")
    su.append(["Setting", "Value"])
    for c in su[1]:
        c.font, c.fill = WHITE, HEAD
    for key, lbl in SETUP_KEYS:
        su.append([lbl, setup.get(key, "")])
    su.column_dimensions["A"].width = 32
    su.column_dimensions["B"].width = 60

    leads = sorted(leads, key=lambda r: (num(r.get("fraud_score")) if num(r.get("fraud_score")) is not None else 100,
                                         -(num(r.get("avg_views")) or 0)))
    table(wb.create_sheet("Leads"), LEAD_COLS, leads, "verdict",
          [22, 26, 10, 12, 11, 10, 11, 10, 13, 10, 14, 60, 22, 13, 12, 9, 9, 9, 30, 40, 11])
    for row in wb["Leads"].iter_rows(min_row=2):
        row[LEAD_COLS.index("reasons")].alignment = Alignment(wrap_text=True, vertical="top")
    table(wb.create_sheet("Ad log"), AD_COLS, ads, "verdict", [22, 12, 10, 9, 19, 10, 40])
    table(wb.create_sheet("Drafts"), DRAFT_COLS, EXTRA["drafts"], "state", [11, 7, 8, 22, 20, 30, 90, 10])
    table(wb.create_sheet("Activity"), ACT_COLS, EXTRA["activity"], "agent", [11, 7, 12, 110])
    table(wb.create_sheet("Ideas"), IDEA_COLS, EXTRA["ideas"], "status", [11, 36, 90, 12])
    wb.save(book)


# ---------------- ad verdicts ----------------
def rate_ads(ads):
    priced = []
    for a in ads:
        cost, joined = num(a.get("cost_usd")), num(a.get("joined"))
        if not joined:
            a["cost_per_subscriber"], a["verdict"] = "none joined", "avoid"
        else:
            a["cost_per_subscriber"] = round(cost / joined, 2) if cost is not None else ""
            if joined < 20:
                a["verdict"] = "avoid"
            elif cost is not None:
                priced.append(a)
    priced.sort(key=lambda a: a["cost_per_subscriber"])
    n = len(priced)
    for i, a in enumerate(priced):
        a["verdict"] = "rebook" if i < max(1, n // 3) else ("avoid" if n >= 3 and i >= n - n // 3 else "ok")
    return ads


# ---------------- commands ----------------
def cmd_setup(a):
    setup, leads, ads = load(a.book)
    for key, _ in SETUP_KEYS:
        v = getattr(a, key, None)
        if v not in (None, ""):
            setup[key] = v
    setup.setdefault("size", "5000-150000")
    save(a.book, setup, leads, ads)
    print(f"Saved setup in {a.book}")


def cmd_add(a):
    setup, leads, ads = load(a.book)
    have = {str(r["username"]).lower().lstrip("@") for r in leads}
    added = 0
    with open(a.csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r.get("username") or "").lower().lstrip("@").strip()
            if not key or key in have:
                continue
            reach, pts, verdict, why = score(r)
            v = num(r.get("recent_views")) or num(r.get("avg_views"))
            r.update({"username": "@" + key, "reach_percent": round(reach * 100, 1) if reach is not None else "",
                      "fair_price_usd": f"${v / 1000 * 8:,.0f}-{v / 1000 * 20:,.0f}" if v else "",
                      "fraud_score": pts, "verdict": verdict, "reasons": why, "status": "new",
                      "added_on": date.today().isoformat()})
            for k in ("subscribers", "avg_views", "recent_views", "er_percent", "growth_7d", "growth_30d"):
                if num(r.get(k)) is not None:
                    r[k] = num(r[k])
            leads.append(r); have.add(key); added += 1
    save(a.book, setup, leads, ads)
    counts = {v: sum(1 for r in leads if r.get("verdict") == v) for v in ("clean", "check by hand", "risky")}
    print(f"Added {added} new channels. Leads now {len(leads)}: {counts}")


def cmd_status(a):
    if a.status not in STATUSES:
        sys.exit(f"status must be one of {STATUSES}")
    setup, leads, ads = load(a.book)
    key = a.channel.lower().lstrip("@")
    for r in leads:
        if str(r["username"]).lower().lstrip("@") == key:
            r["status"] = a.status
            if a.price is not None:
                r["agreed_price"] = a.price
            save(a.book, setup, leads, ads)
            print(f"{r['username']} -> {a.status}")
            return
    sys.exit(f"{a.channel} is not in Leads")


def cmd_ad(a):
    setup, leads, ads = load(a.book)
    ads.append({"channel": "@" + a.channel.lstrip("@"), "date": a.date, "cost_usd": a.cost, "joined": a.joined,
                "notes": a.notes or ""})
    rate_ads(ads)
    for r in leads:
        if str(r["username"]).lower() == ("@" + a.channel.lstrip("@")).lower():
            r["status"] = "done"
    save(a.book, setup, leads, ads)
    print_summary(setup, leads, ads)


def print_summary(setup, leads, ads):
    print("SETUP:", {k: v for k, v in setup.items() if v not in ("", None)} or "not set yet")
    counts = {v: sum(1 for r in leads if r.get("verdict") == v) for v in ("clean", "check by hand", "risky")}
    stat = {s: sum(1 for r in leads if r.get("status") == s) for s in STATUSES}
    print(f"LEADS: {len(leads)} {counts} by status {stat}")
    print(f"DRAFTS WAITING: {sum(1 for x in EXTRA['drafts'] if x.get('state') == 'waiting')} · IDEAS: {len(EXTRA['ideas'])}")
    for r in [r for r in leads if r.get("verdict") == "clean" and r.get("status") == "new"][:10]:
        print(f"  clean, not contacted: {r['username']} subs {r.get('subscribers')} views {r.get('avg_views')} "
              f"fair {r.get('fair_price_usd')} contact {r.get('admin_contact') or '?'}")
    if ads:
        spent = sum(num(x.get("cost_usd")) or 0 for x in ads)
        month = date.today().strftime("%Y-%m")
        spent_m = sum(num(x.get("cost_usd")) or 0 for x in ads if str(x.get("date", "")).startswith(month))
        print(f"ADS: {len(ads)} booked, ${spent:,.0f} total, ${spent_m:,.0f} this month"
              + (f", ${num(setup.get('monthly')) - spent_m:,.0f} left of monthly budget" if num(setup.get("monthly")) else ""))
        for x in sorted(ads, key=lambda x: (x["cost_per_subscriber"] if isinstance(x["cost_per_subscriber"], (int, float)) else 1e9)):
            print(f"  {x['channel']} {x['date']} ${x['cost_usd']} joined {x['joined']} -> {x['cost_per_subscriber']} ({x['verdict']})")


def cmd_show(a):
    if not os.path.exists(a.book):
        print("NO WORKBOOK YET: run the first-time setup")
        return
    print_summary(*load(a.book))


# ---------------- crew activity, drafts, ideas, dashboard ----------------
def now_parts():
    from datetime import datetime
    t = datetime.now()
    return t.date().isoformat(), t.strftime("%H:%M")


def cmd_log(a):
    setup, leads, ads = load(a.book)
    key = AGENT_KEYS.get(a.agent.lower())
    if not key:
        sys.exit(f"agent must be one of {sorted(set(AGENT_KEYS))}")
    d, t = now_parts()
    EXTRA["activity"].append({"date": d, "time": t, "agent": key, "text": a.text})
    save(a.book, setup, leads, ads)
    print(f"logged {key}: {a.text[:60]}")


def cmd_draft(a):
    setup, leads, ads = load(a.book)
    text = open(a.textfile, encoding="utf-8").read().strip() if os.path.exists(a.textfile) else a.textfile
    d, t = now_parts()
    EXTRA["drafts"].append({"date": d, "time": t, "kind": "post" if a.kind == "post" else "dm", "channel": a.channel,
                            "to": a.to, "title": a.title, "text": text, "state": "waiting"})
    save(a.book, setup, leads, ads)
    print(f"draft saved for {a.channel}")


def cmd_welcome(a):
    setup, leads, ads = load(a.book)
    text = open(a.textfile, encoding="utf-8").read().strip() if os.path.exists(a.textfile) else a.textfile
    if "%username%" not in text and "%firstname%" not in text:
        sys.exit("The welcome message needs %username% or %firstname% so each person is greeted by name")
    setup["welcome"] = text
    save(a.book, setup, leads, ads)
    print("welcome message saved:", text.replace("%username%", "@alex_crypto").replace("%firstname%", "Alex")[:120])


def cmd_drafted(a):
    setup, leads, ads = load(a.book)
    for x in EXTRA["drafts"]:
        if x.get("state") == "waiting":
            x["state"] = "handled"
    save(a.book, setup, leads, ads)
    print("waiting drafts marked handled")


def cmd_idea(a):
    setup, leads, ads = load(a.book)
    d, _ = now_parts()
    EXTRA["ideas"].append({"date": d, "idea": a.idea, "details": a.details, "status": a.status})
    save(a.book, setup, leads, ads)
    print("idea saved")


def latest_run(activity):
    """The crew's latest working day as one task the dashboard replays."""
    if not activity:
        return []
    day = max(str(e.get("date")) for e in activity)
    todays = [e for e in activity if str(e.get("date")) == day]
    steps, results, title = [], {}, None
    for e in todays:
        k = e.get("agent")
        if k == "nav":
            title = title or e.get("text")
            continue
        if k not in steps:
            steps.append(k)
        results[k] = (results.get(k, "") + " " + str(e.get("text"))).strip()
    if not steps:
        return []
    return [{"text": title or "Today's work", "steps": steps, "results": results}]


def cmd_dashboard(a):
    import json
    setup, leads, ads = load(a.book)
    here = os.path.dirname(os.path.abspath(__file__))
    tpl = next((t for t in (os.path.join(here, "..", "assets", "agent-world.html"),
                            os.path.join(here, "agent-world-template.html"), "/mnt/data/agent-world-template.html",
                            "agent-world-template.html") if os.path.exists(t)), None)
    if not tpl:
        sys.exit("dashboard template not found (agent-world-template.html)")
    html = open(tpl, encoding="utf-8").read()
    clean = lambda rows: [{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in r.items()} for r in rows]
    d, _ = now_parts()
    data = {"date": d, "setup": setup, "leads": clean(leads), "ads": clean(ads),
            "drafts": [x for x in clean(EXTRA["drafts"]) if x.get("state") == "waiting"],
            "activity": clean(EXTRA["activity"])[-60:], "ideas": clean(EXTRA["ideas"]),
            "run": latest_run(clean(EXTRA["activity"])), "brain": a.brain}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    marker = "window.REAL=null;/*__REAL__*/"
    if marker not in html:
        sys.exit("dashboard template is missing its data marker")
    open(a.out, "w", encoding="utf-8").write(html.replace(marker, "window.REAL=" + blob + ";"))
    print(f"Wrote {a.out}: {len(leads)} leads, {len(ads)} ads, {len(data['drafts'])} drafts waiting, "
          f"replays {len(data['run'][0]['steps']) if data['run'] else 0} crew steps")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup"); s.add_argument("book")
    for key, _ in SETUP_KEYS:
        s.add_argument("--" + key)
    s.set_defaults(fn=cmd_setup)
    s = sub.add_parser("add"); s.add_argument("book"); s.add_argument("csv"); s.set_defaults(fn=cmd_add)
    s = sub.add_parser("status"); s.add_argument("book"); s.add_argument("channel"); s.add_argument("status")
    s.add_argument("--price", type=float); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("ad"); s.add_argument("book"); s.add_argument("channel"); s.add_argument("date")
    s.add_argument("cost", type=float); s.add_argument("joined", type=int); s.add_argument("--notes")
    s.set_defaults(fn=cmd_ad)
    s = sub.add_parser("show"); s.add_argument("book"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("log"); s.add_argument("book"); s.add_argument("agent"); s.add_argument("text"); s.set_defaults(fn=cmd_log)
    s = sub.add_parser("draft"); s.add_argument("book"); s.add_argument("kind", choices=["dm", "post"])
    s.add_argument("channel"); s.add_argument("to"); s.add_argument("title"); s.add_argument("textfile")
    s.set_defaults(fn=cmd_draft)
    s = sub.add_parser("welcome"); s.add_argument("book"); s.add_argument("textfile"); s.set_defaults(fn=cmd_welcome)
    s = sub.add_parser("drafted"); s.add_argument("book"); s.set_defaults(fn=cmd_drafted)
    s = sub.add_parser("idea"); s.add_argument("book"); s.add_argument("idea"); s.add_argument("details")
    s.add_argument("--status", default="suggested"); s.set_defaults(fn=cmd_idea)
    s = sub.add_parser("dashboard"); s.add_argument("book"); s.add_argument("out")
    s.add_argument("--brain", default="Claude", help="name of the chat app shown in the page")
    s.set_defaults(fn=cmd_dashboard)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
