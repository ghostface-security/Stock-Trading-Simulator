#!/bin/bash
set -e

# Define log file names
STATUS_LOG="systemctl_status_log.txt"
JOURNAL_LOG="journalctl_service_log.txt"

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Restart the stock-trading-sim service
echo "Restarting the stock-trading-sim service..."
sudo systemctl restart stock-trading-sim.service

# Check the status and write to the log file
echo "Checking service status and saving to $STATUS_LOG..."
sudo systemctl status stock-trading-sim.service > "$STATUS_LOG"

# Check the journal logs and write to a log file (last 50 lines)
echo "Fetching the last 50 journal logs and saving to $JOURNAL_LOG..."
sudo journalctl -u stock-trading-sim.service -n 50 --no-pager > "$JOURNAL_LOG"

echo "Service restart completed. Status is in $STATUS_LOG and logs are in $JOURNAL_LOG"
