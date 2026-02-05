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

# Launch Chromium in maximized window (not kiosk, so user can exit)
chromium-browser --start-maximized --incognito --noerrdialogs --disable-infobars --no-first-run http://127.0.0.1:5001
