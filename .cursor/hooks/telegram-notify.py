#!/usr/bin/env python3
"""Send a Telegram notification when a Cursor agent task completes."""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATUS_EMOJI = {
    "completed": "✅",
    "error": "❌",
    "aborted": "⏹️",
}

EVENT_LABELS = {
    "stop": "Agent task",
    "subagentStop": "Subagent task",
}


def config_paths() -> list[Path]:
    paths = []
    env_path = os.environ.get("CURSOR_TELEGRAM_CONFIG")
    if env_path:
        paths.append(Path(env_path).expanduser())

    paths.extend(
        [
            Path.cwd() / ".cursor" / "telegram-notify.config.json",
            Path.home() / ".cursor" / "telegram-notify.config.json",
        ]
    )
    return paths


def load_config() -> dict:
    config: dict = {}

    for path in config_paths():
        if not path.is_file():
            continue
        try:
            with path.open(encoding="utf-8") as handle:
                file_config = json.load(handle)
            if isinstance(file_config, dict):
                config.update(file_config)
                break
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[telegram-notify] Failed to read config {path}: {exc}", file=sys.stderr)

    token = os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("bot_token")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or config.get("chat_id")

    notify_on = config.get("notify_on", ["completed", "error"])
    if isinstance(notify_on, str):
        notify_on = [notify_on]

    messages = config.get("messages", {})
    if not isinstance(messages, dict):
        messages = {}

    return {
        "bot_token": token,
        "chat_id": chat_id,
        "notify_on": {str(status).lower() for status in notify_on},
        "include_workspace": bool(config.get("include_workspace", True)),
        "include_model": bool(config.get("include_model", True)),
        "include_subagents": bool(config.get("include_subagents", True)),
        "message_prefix": str(config.get("message_prefix", "Cursor")),
        "messages": {str(key).lower(): str(value) for key, value in messages.items()},
    }


def workspace_label(payload: dict) -> str:
    roots = payload.get("workspace_roots") or []
    if not roots:
        return "Unknown workspace"

    root = Path(str(roots[0]))
    return root.name or str(root)


def render_template(template: str, payload: dict, config: dict) -> str:
    status = str(payload.get("status", "unknown")).lower()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    replacements = {
        "{status}": status,
        "{workspace}": workspace_label(payload),
        "{time}": timestamp,
        "{model}": str(payload.get("model") or ""),
    }
    message = template
    for key, value in replacements.items():
        message = message.replace(key, value)
    return message


def build_message(payload: dict, config: dict) -> str:
    event = str(payload.get("hook_event_name", "stop"))
    status = str(payload.get("status", "unknown")).lower()

    custom = config.get("messages", {}).get(status)
    if custom:
        return render_template(custom, payload, config)

    emoji = STATUS_EMOJI.get(status, "ℹ️")
    label = EVENT_LABELS.get(event, "Task")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"{emoji} *{config['message_prefix']} {label} {status}*",
        "",
        f"Status: `{status}`",
        f"Time: `{timestamp}`",
    ]

    if config["include_workspace"]:
        lines.append(f"Workspace: `{workspace_label(payload)}`")

    if config["include_model"] and payload.get("model"):
        lines.append(f"Model: `{payload['model']}`")

    if event == "subagentStop":
        subagent_type = payload.get("subagent_type")
        if subagent_type:
            lines.append(f"Subagent: `{subagent_type}`")

    conversation_id = payload.get("conversation_id")
    if conversation_id:
        lines.append(f"Conversation: `{conversation_id[:8]}...`")

    return "\n".join(lines)


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram API returned HTTP {response.status}")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"[telegram-notify] Invalid hook input: {exc}", file=sys.stderr)
        return 0

    event = str(payload.get("hook_event_name", "stop"))
    config = load_config()

    if event == "subagentStop" and not config["include_subagents"]:
        return 0

    status = str(payload.get("status", "unknown")).lower()
    if status not in config["notify_on"]:
        return 0

    token = config.get("bot_token")
    chat_id = config.get("chat_id")
    if not token or not chat_id:
        print(
            "[telegram-notify] Missing bot_token or chat_id. "
            "Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID or create "
            "~/.cursor/telegram-notify.config.json",
            file=sys.stderr,
        )
        return 0

    message = build_message(payload, config)

    try:
        send_telegram_message(token, chat_id, message)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"[telegram-notify] Failed to send notification: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
