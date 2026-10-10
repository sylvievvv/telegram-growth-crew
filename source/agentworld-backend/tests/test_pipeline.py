"""Offline tests: fraud scoring, contact finding and the Scout pipeline with a fake TGStat.

Run:  python -m pytest -q   (or: python tests/test_pipeline.py)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import fraud  # noqa: E402
import scout  # noqa: E402


def hist(counts):
    return [{"period": f"2026-10-{i + 1:02d}", "participants_count": c} for i, c in enumerate(counts)]


def test_clean_channel():
    s, r = fraud.score_channel({"participants_count": 20000, "avg_post_reach": 4200, "err_percent": 21, "er_percent": 1.2},
                               hist([19500 + 50 * i for i in range(10)]))
    assert s < 30, (s, r)


def test_fake_subscribers():
    s, r = fraud.score_channel({"participants_count": 140000, "avg_post_reach": 2100, "err_percent": 1.5},
                               hist([100000] * 5 + [131000, 140000, 140000, 140000, 140000]))
    assert s >= 60, (s, r)
    assert any("jump" in x for x in r)


def test_contacts():
    about = "Crypto news daily.\nРеклама / ads: @ads_manager_x\nChat: t.me/our_chat_room"
    assert scout.find_contacts(about, "mychannel")[0] == "@ads_manager_x"


class FakeTGStat:
    def search(self, q=None, category=None, limit=50):
        return [
            {"username": "@goodchan", "title": "Good Chan", "participants_count": 20000, "about": "ads: @good_ads"},
            {"username": "@fakechan", "title": "Fake Chan", "participants_count": 150000, "about": ""},
            {"username": "@tiny", "title": "Tiny", "participants_count": 500, "about": ""},
        ]

    def stat(self, ch):
        return {"@goodchan": {"participants_count": 20000, "avg_post_reach": 4000, "err_percent": 20, "er_percent": 1.0},
                "@fakechan": {"participants_count": 150000, "avg_post_reach": 2500, "err_percent": 1.6}}[ch]

    def subscribers(self, ch, days=30):
        return hist([19800 + 30 * i for i in range(10)]) if ch == "@goodchan" else hist([90000] * 6 + [150000] * 4)


def test_pipeline():
    res = scout.run_scout(["crypto"], api=FakeTGStat())
    assert [l["username"] for l in res["clean_or_check"]] == ["@goodchan"]
    assert [l["username"] for l in res["risky"]] == ["@fakechan"]
    assert res["clean_or_check"][0]["admin_contacts"] == ["@good_ads"]
    again = scout.run_scout(["crypto"], api=FakeTGStat())  # already saved: nothing new
    assert not again["clean_or_check"] and not again["risky"]
    print(scout.summary_text(res))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
