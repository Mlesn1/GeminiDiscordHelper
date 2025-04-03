#!/bin/bash

# This script is designed to ONLY run the Discord bot
# It will not start the Flask web interface
# This prevents port conflicts

echo "============================================================"
echo "STARTING DISCORD BOT IN STANDALONE MODE (NO FLASK)"
echo "============================================================"

# Export variable to signal we are running the Discord bot workflow
export DISCORD_BOT_WORKFLOW=1

# Run the clean Discord bot
python clean_bot.py
