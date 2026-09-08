# Cursor Telegram Notify

Get a Telegram message whenever Cursor finishes an agent task.

This uses **Cursor Hooks** (not a VS Code extension). Hooks run when the agent loop ends and call the Telegram Bot API.

## What you get

- Notification when an **agent task** completes (`stop` hook)
- Optional notification when a **subagent** finishes (`subagentStop` hook)
- Status-aware messages: completed, error, aborted
- Workspace name, model, and timestamp in the message

Example message:

```text
✅ Cursor Agent task completed

Status: completed
Time: 2026-09-08 10:15 UTC
Workspace: my-project
Model: claude-4-sonnet
```

## Setup

### 1. Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** (looks like `123456789:ABCdef...`)

### 2. Get your chat ID

1. Message your new bot (send any text)
2. Open this URL in a browser (replace `YOUR_BOT_TOKEN`):

   `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`

3. Find `"chat":{"id":123456789}` in the JSON — that number is your **chat ID**

### 3. Install

**Option A — This project only (recommended for one repo)**

```bash
cp .cursor/telegram-notify.config.json.example .cursor/telegram-notify.config.json
# Edit .cursor/telegram-notify.config.json with your token and chat_id
```

Hooks in `.cursor/hooks.json` are already wired. Restart Cursor or save `hooks.json` to reload.

**Option B — All projects (user-level)**

```bash
chmod +x install-user.sh
./install-user.sh
# Edit ~/.cursor/telegram-notify.config.json
```

### 4. Configure

Copy the example config and fill in your values:

```json
{
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID",
  "notify_on": ["completed", "error"],
  "include_workspace": true,
  "include_model": true,
  "include_subagents": true,
  "message_prefix": "Cursor"
}
```

| Field | Description |
|-------|-------------|
| `bot_token` | Telegram bot token from BotFather |
| `chat_id` | Your Telegram chat ID |
| `notify_on` | Statuses to notify: `completed`, `error`, `aborted` |
| `include_subagents` | Notify when Task/subagent runs finish |
| `message_prefix` | Prefix shown in the notification title |

**Environment variables** (override config file):

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CURSOR_TELEGRAM_CONFIG` — path to a custom config file

## Test

Simulate a completed task:

```bash
echo '{"hook_event_name":"stop","status":"completed","loop_count":0,"workspace_roots":["/tmp/demo"],"model":"test-model","conversation_id":"abc-123"}' \
  | python3 .cursor/hooks/telegram-notify.py
```

You should receive a Telegram message within a few seconds.

## Troubleshooting

1. **No message** — Check Cursor **Output → Hooks** for errors
2. **Missing config** — Ensure `bot_token` and `chat_id` are set
3. **Hook not running** — Restart Cursor; confirm `.cursor/hooks.json` exists
4. **Script not executable** — Run `chmod +x .cursor/hooks/telegram-notify.py`

Hooks fail open: if Telegram is unreachable, the agent still finishes normally.

## Files

```text
.cursor/
  hooks.json                          # Hook registration
  hooks/telegram-notify.py            # Notification script
  telegram-notify.config.json.example # Config template
install-user.sh                       # Install to ~/.cursor/
```

## How it works

Cursor fires the `stop` hook when an agent conversation ends. The script reads JSON from stdin, builds a message, and POSTs to `api.telegram.org`. No extra dependencies — Python 3 stdlib only.

## Uninstall

**Project:** Remove the `stop` and `subagentStop` entries from `.cursor/hooks.json`.

**User-level:** Remove `./hooks/telegram-notify.py` from `~/.cursor/hooks.json` and delete `~/.cursor/hooks/telegram-notify.py`.
