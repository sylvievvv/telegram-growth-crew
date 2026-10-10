"""Offline test: fake Telegram, real MCP server over HTTP. Run: python test_server.py"""
import asyncio
import json
import os
import sys
import tempfile

os.environ.update(CONNECTOR_SECRET="x" * 32, POSTING_BOT_TOKEN="p", TRACKING_BOT_TOKEN="t", CHANNEL_ID="@demo",
                  DB_PATH=os.path.join(tempfile.mkdtemp(), "t.db"), PORT="8765",
                  WELCOME_GROUP_ID="-1009")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server  # noqa: E402

SENT = []
UPDATES = [[{"update_id": 1, "chat_member": {"date": 1, "invite_link": {"invite_link": "https://t.me/+abc"},
             "new_chat_member": {"status": "member", "user": {"id": 7}}, "old_chat_member": {"status": "left", "user": {"id": 7}}}},
            {"update_id": 2, "chat_member": {"date": 2, "invite_link": {"invite_link": "https://t.me/+abc"},
             "new_chat_member": {"status": "member", "user": {"id": 8}}, "old_chat_member": {"status": "left", "user": {"id": 8}}}},
            {"update_id": 3, "chat_member": {"date": 3,
             "new_chat_member": {"status": "left", "user": {"id": 8}}, "old_chat_member": {"status": "member", "user": {"id": 8}}}},
            {"update_id": 4, "chat_join_request": {"date": 4, "chat": {"id": -1001}, "user_chat_id": 55,
             "from": {"id": 55, "first_name": "Ana", "username": "ana_defi"}, "invite_link": {"invite_link": "https://t.me/+abc"}}},
            {"update_id": 5, "chat_member": {"date": 5, "chat": {"id": -1009},
             "new_chat_member": {"status": "member", "user": {"id": 66, "first_name": "Bob"}},
             "old_chat_member": {"status": "left", "user": {"id": 66}}}}]]


async def fake_tg(token, method, **p):
    SENT.append((token, method, p))
    if method == "getChat":
        return {"title": "Demo", "username": "demo"}
    if method == "getChatMemberCount":
        return 18420
    if method == "sendMessage":
        return {"message_id": 99}
    if method == "approveChatJoinRequest":
        return True
    if method == "createChatInviteLink":
        return {"invite_link": "https://t.me/+abc"}
    if method == "getUpdates":
        if UPDATES:
            return UPDATES.pop()
        await asyncio.sleep(3600)
    raise AssertionError(method)


server.tg = fake_tg


async def main():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    import uvicorn
    app = server.mcp.streamable_http_app()
    srv = uvicorn.Server(uvicorn.Config(app, port=8765, log_level="warning"))
    t = asyncio.create_task(srv.serve())
    listener = asyncio.create_task(server.listen_for_joins())
    await asyncio.sleep(1)
    url = f"http://127.0.0.1:8765/{'x' * 32}/mcp"
    async with streamablehttp_client(url) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = sorted(t.name for t in (await s.list_tools()).tools)
            print("tools:", tools)
            call = lambda n, **a: s.call_tool(n, a)
            out = lambda res: json.loads(res.content[0].text)
            print("overview:", out(await call("channel_overview")))
            pv = out(await call("post_to_channel", text="Weekly poll: what next?"))
            assert pv["posted"] is False and "preview" in pv, pv
            assert not any(m == "sendMessage" and tk == "p" for tk, m, _ in SENT), "posted without confirm!"
            bad = out(await call("post_to_channel", text="Partner post, join now", is_paid_promo=True, confirmed=True))
            assert bad["posted"] is False and bad["problems"], bad
            sig = out(await call("post_to_channel", text="BTC buy now, price target 200k", confirmed=True))
            assert sig["posted"] is False, sig
            ok = out(await call("post_to_channel", text="#ad Paid partnership: @layer2brief", is_paid_promo=True, confirmed=True))
            assert ok["posted"] and [tk for tk, m, _ in SENT if m == "sendMessage" and tk == "p"] == ["p"], (ok, SENT)
            print("ad link:", out(await call("create_ad_link", ad_name="ad criptonoticias oct")))
            await asyncio.sleep(0.5)
            res = await call("ad_results")
            results = [json.loads(c.text) for c in res.content]
            print("results:", results)
            assert results[0]["joined"] == 3, results  # 2 normal joins + 1 approved join request
            dms = [p for tk, m, p in SENT if m == "sendMessage" and tk == "t"]
            print("welcomes:", dms)
            assert dms[0]["chat_id"] == 55 and "@ana_defi" in dms[0]["text"], dms
            assert dms[1]["chat_id"] == -1009 and "Bob" in dms[1]["text"], dms
            assert any(m == "approveChatJoinRequest" for _, m, _ in SENT)
            link = [p for _, m, p in SENT if m == "createChatInviteLink"][0]
            assert link.get("creates_join_request") is True, link
            w = out(await call("welcome_message"))
            print("welcome now:", w)
            bad = out(await call("welcome_message", new_text="Hi there, buy now and 100x", confirmed=True))
            assert bad["saved"] is False, bad
            pv = out(await call("welcome_message", new_text="Bienvenido %username%! Lee el post fijado."))
            assert pv["saved"] is False and "@alex_crypto" in pv["preview"], pv
            ok = out(await call("welcome_message", new_text="Bienvenido %username%! Lee el post fijado.", confirmed=True))
            assert ok["saved"] and out(await call("welcome_message"))["welcome_message"].startswith("Bienvenido"), ok
    listener.cancel()
    srv.should_exit = True
    await t
    print("ALL OK")


asyncio.run(main())
