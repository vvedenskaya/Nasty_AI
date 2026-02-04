# Raspberry Pi Deployment Guide

This directory contains all the configuration files needed to set up the WASP chatbot on a Raspberry Pi with automatic startup.

## Files Overview

- `wasp-bot-browser.sh` - Browser launch script with server readiness check
- `wasp_bot_browser.desktop` - Desktop autostart entry
- `wasp_bot.service` - Systemd service for Flask server
- `DEPLOY.md` - This file

## Installation Steps

### 1. Copy Browser Script

```bash
# Create bin directory if it doesn't exist
mkdir -p ~/bin

# Copy the script
cp pi_setup/wasp-bot-browser.sh ~/bin/

# Make it executable
chmod +x ~/bin/wasp-bot-browser.sh
```

### 2. Copy Desktop Entry

```bash
# Create autostart directory if it doesn't exist
mkdir -p ~/.config/autostart

# Copy the desktop entry
cp pi_setup/wasp_bot_browser.desktop ~/.config/autostart/

# Set correct ownership and permissions
chown $USER:$USER ~/.config/autostart/wasp_bot_browser.desktop
chmod +x ~/.config/autostart/wasp_bot_browser.desktop
```

### 3. Install Systemd Service

```bash
# Copy service file to systemd directory
sudo cp pi_setup/wasp_bot.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable wasp_bot.service

# Start the service
sudo systemctl start wasp_bot.service

# Check status
sudo systemctl status wasp_bot.service
```

### 4. Configure Auto Login (Important!)

For the browser to auto-start, the Raspberry Pi must automatically log in to the desktop:

```bash
sudo raspi-config
```

Navigate to:
- `1 System Options`
- `S5 Boot / Auto Login`
- Select `B4 Desktop Autologin`

### 5. Verify Installation

After rebooting (`sudo reboot`), the system should:
1. Start the Flask server automatically (via systemd)
2. Wait for the server to be ready (via the bash script)
3. Open Chromium in kiosk mode after ~4 seconds of server readiness

## Troubleshooting

### Check Server Status
```bash
sudo systemctl status wasp_bot.service
```

### View Browser Logs
```bash
cat /home/mancy/var/log/wasp-bot-browser.log
```

### View Server Logs
```bash
sudo journalctl -u wasp_bot.service -f
```

### Manual Browser Launch
If autostart isn't working, test manually:
```bash
~/bin/wasp-bot-browser.sh
```

### Check Desktop Entry
```bash
cat ~/.config/autostart/wasp_bot_browser.desktop
```

## Notes

- The script waits for the Flask server to respond before launching the browser
- Screen blanking is disabled to prevent the display from turning off
- Browser runs in incognito mode to avoid cache issues
- All browser output is logged to `/home/mancy/var/log/wasp-bot-browser.log`
