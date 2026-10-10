"""Offline test for the welcome message. Run: python -m pytest -q"""
import asyncio
import os
import sys
import tempfile
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "w.db")
os.environ["WELCOME_GROUP_ID"] = "-1009"

import db  # noqa: E402
import welcome  # noqa: E402

db.init()


class Bot:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


def test_fill():
    assert welcome.fill("Welcome %username%!", NS(first_name="Ana", username="ana_defi")) == "Welcome @ana_defi!"
    assert welcome.fill("Hi %username%", NS(first_name="Bob", username=None)) == "Hi Bob"
    assert welcome.problems("Welcome! buy now")  # signal + no name
    assert not welcome.problems("Bienvenido %username%!")


def test_join_request_and_group():
    bot = Bot()
    approved = []

    async def approve():
        approved.append(True)
    req = NS(approve=approve, user_chat_id=55, from_user=NS(first_name="Ana", username="ana_defi"))
    asyncio.run(welcome.on_join_request(NS(chat_join_request=req), NS(bot=bot)))
    assert approved and bot.sent[0][0] == 55 and "@ana_defi" in bot.sent[0][1]

    db.set_setting("welcome", "Bienvenido %firstname%!")
    cm = NS(chat=NS(id=-1009, username=None), old_chat_member=NS(status="left"),
            new_chat_member=NS(status="member", user=NS(first_name="Bob", username=None)))
    asyncio.run(welcome.on_group_member(NS(chat_member=cm), NS(bot=bot)))
    assert bot.sent[1] == (-1009, "Bienvenido Bob!")
    other = NS(chat=NS(id=-1001, username="other"), old_chat_member=NS(status="left"),
               new_chat_member=NS(status="member", user=NS(first_name="Cy", username=None)))
    asyncio.run(welcome.on_group_member(NS(chat_member=other), NS(bot=bot)))
    assert len(bot.sent) == 2


if __name__ == "__main__":
    test_fill(); test_join_request_and_group(); print("ALL OK")
