# Telegram Growth connector (Option B)

A small server that lets the owner's **own Claude** use his Telegram bots. There is no Claude API key and no extra AI bill: the thinking happens in his normal Claude subscription. This server only talks to Telegram.

Once it is connected, the owner can say in Claude:

| He says | Claude uses | What happens |
|---|---|---|
| "How many subscribers do I have?" | `channel_overview` | Reads the channel's subscriber count |
| "Post the weekly poll" | `post_to_channel` | Claude shows a preview first. The post only goes out through his **existing bot** after he says yes. |
| "Make an invite link for the ad on @criptonoticias" | `create_ad_link` | Creates a named link for that ad |
| "How did my ads do?" | `ad_results` | Shows joins per ad link, and how many of them already left |
| "Change my welcome message to: Welcome %username%! …" | `welcome_message` | Shows a preview with an example name. It is saved only after he says yes. |

## Welcome message ("Welcome %username%!")

Every new member can get a personal welcome:
- **People who join through an ad link** made with `create_ad_link`. The link is a "request to join" link: the bot approves them right away (they hardly notice) and sends them the welcome message in a private chat.
- **New members of his discussion group** (optional). Set `WELCOME_GROUP_ID` to the group, and make the new bot admin there. The bot greets them in the group by name.

`%username%` becomes their @username, or their first name if they have none. `%firstname%` is always the first name.

What Telegram does not allow: a bot cannot message people who join a public channel straight through its @username or a normal link. Those people see the pinned welcome post instead. Ask Claude to write one with "Draft a welcome post".

To switch the welcome off on ad links, set `WELCOME_ON_AD_LINKS=no`. Ad links are then normal links, and joins are still counted.

Built-in rules, enforced by the server whatever Claude does:
- No post goes out without a second call with `confirmed=true`.
- Buy/sell signals and profit promises are refused.
- Paid promos are refused unless they are marked `#ad` / "Paid partnership".

## Why two bots

| Bot | Token | What it does here |
|---|---|---|
| His **existing** bot | `POSTING_BOT_TOKEN` | Only *sends* posts. It does not read any updates, so his current bot keeps working exactly as before. |
| A **new** "Agent World" bot | `TRACKING_BOT_TOKEN` | Makes the ad links and listens for joins. |

Telegram allows only one program to read a bot's updates. If the existing bot were used for tracking, it would break the copy/paste bot he already runs. So never put the existing token in `TRACKING_BOT_TOKEN`.

## Setup (about 30 minutes)

1. **New bot:** in Telegram, @BotFather → `/newbot`. Copy the token.
2. **Channel admins:** add both bots as admins of the channel.
   - Existing bot: "Post messages".
   - New bot: "Invite users via link" (also needed to approve join requests for the welcome message).
   - Optional: make the new bot admin of the discussion group too, for welcomes in the group.
3. **Server:** any always-on machine with a public **HTTPS** address, for example a small VPS behind Caddy, or Railway, Render or Fly.io.
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env     # fill it in
   python test_server.py    # offline test with a fake Telegram, should end with ALL OK
   python server.py         # listens on PORT (default 8080)
   ```
   Keep it running with systemd, pm2 or Docker.
4. **Connector URL:**
   `https://your-domain/<CONNECTOR_SECRET>/mcp`
   - The secret in the URL is the password. Use 32+ random characters, for example `openssl rand -hex 24`.
   - Never share the URL publicly.
5. **Connect it in Claude:**
   1. The owner opens Settings → Connectors → **Add custom connector** and pastes the URL.
   2. In a chat, he clicks + → Connectors and switches "Telegram Growth" on.

## Good to know

- **Joins are only counted while the server is running.** Joins via links made with Telegram's own app (not via `create_ad_link`) are not tracked; he reads those in the app.
- **If Claude insists on a sign-in screen** (custom connectors are in beta), add OAuth with `auth_server_provider` in FastMCP. The secret-URL approach is the simple start.
- **Library version:** this uses `mcp` 1.x. Pin `mcp<2` as in requirements.txt.
- **Don't run Option C at the same time on the same new bot.** If he later wants the fully automatic version (`agentworld-backend`), give that one its own bot token.
