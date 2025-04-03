#!/bin/bash

# This script is specifically for the run_discord_bot workflow
# It ensures that only the Discord bot runs without any Flask application

# Stop any existing Python or gunicorn processes to avoid port conflicts
pkill -f "python.*main.py" || true
pkill -f gunicorn || true
sleep 1

# Run the specialized Discord bot script for workflows
exec python discord_bot_workflow.py
