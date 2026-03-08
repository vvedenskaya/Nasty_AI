#!/bin/bash

set -x

# Disable screen blanking and power management
xset s off
xset -dpms
xset s noblank

# Ensure log directory exists
mkdir -p /home/mancy/var/log

# Redirect all output to log file
exec >/home/mancy/var/log/wasp-bot-browser.log 2>&1

# Wait until Flask server is ready
until curl -s http://127.0.0.1:5001 > /dev/null;
do
        sleep 1;
done;

# Additional small delay to ensure server is fully ready
sleep 4

# Use a clean temporary profile on each launch.
# This prevents Chromium from showing "Restore pages" after unclean shutdowns.
CHROME_PROFILE="/tmp/wasp-chromium-profile"
rm -rf "$CHROME_PROFILE"
mkdir -p "$CHROME_PROFILE"

# Launch Chromium with visible UI (toolbar and tabs visible so user can navigate)
# Flags prevent session-restore and first-run interruptions.
chromium-browser \
  --user-data-dir="$CHROME_PROFILE" \
  --noerrdialogs \
  --disable-infobars \
  --no-first-run \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --no-default-browser-check \
  http://127.0.0.1:5001
