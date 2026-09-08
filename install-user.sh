#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_DIR="${HOME}/.cursor"
HOOKS_DIR="${CURSOR_DIR}/hooks"

echo "Installing Cursor Telegram Notify to ${CURSOR_DIR}"

mkdir -p "${HOOKS_DIR}"

cp "${ROOT_DIR}/.cursor/hooks/telegram-notify.py" "${HOOKS_DIR}/telegram-notify.py"
chmod +x "${HOOKS_DIR}/telegram-notify.py"

if [[ ! -f "${CURSOR_DIR}/telegram-notify.config.json" ]]; then
  cp "${ROOT_DIR}/.cursor/telegram-notify.config.json.example" \
    "${CURSOR_DIR}/telegram-notify.config.json"
  echo "Created ${CURSOR_DIR}/telegram-notify.config.json — edit it with your bot token and chat ID."
else
  echo "Keeping existing ${CURSOR_DIR}/telegram-notify.config.json"
fi

HOOKS_JSON="${CURSOR_DIR}/hooks.json"
HOOK_ENTRY='{"command":"./hooks/telegram-notify.py"}'

if [[ ! -f "${HOOKS_JSON}" ]]; then
  cat > "${HOOKS_JSON}" <<'EOF'
{
  "version": 1,
  "hooks": {
    "stop": [
      {
        "command": "./hooks/telegram-notify.py"
      }
    ],
    "subagentStop": [
      {
        "command": "./hooks/telegram-notify.py"
      }
    ]
  }
}
EOF
  echo "Created ${HOOKS_JSON}"
else
  echo "Found existing ${HOOKS_JSON}. Merge the stop/subagentStop entries manually if needed."
fi

echo ""
echo "Done. Next steps:"
echo "1. Edit ${CURSOR_DIR}/telegram-notify.config.json"
echo "2. Restart Cursor (or save hooks.json to reload hooks)"
echo "3. Run an agent task and wait for it to finish"
