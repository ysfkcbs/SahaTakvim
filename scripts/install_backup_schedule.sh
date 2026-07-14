#!/usr/bin/env bash
# Installs a launchd LaunchAgent that runs scripts/backup_postgres.sh daily at 03:00.
# Re-run this any time (e.g. after moving the repo) to regenerate the plist with
# the correct absolute path.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.sahatakvim.backup"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$REPO_DIR/backups"

mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${REPO_DIR}/scripts/backup_postgres.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/backup.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/backup.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "==> Installed and loaded ${LABEL} (daily at 03:00)."
echo "==> Logs: ${LOG_DIR}/backup.log"
echo "==> Run 'launchctl start ${LABEL}' to trigger an immediate test run."
