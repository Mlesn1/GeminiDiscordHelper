#!/bin/bash
# Dedicated script for running the Discord bot in the workflow
# This script ensures that the Discord bot runs without Flask

# Kill any existing processes using port 5000
pkill -f gunicorn || true 
pkill -f "python.*main.py" || true
sleep 1

# Run the dedicated standalone Discord bot script
python start_discord_bot.py
