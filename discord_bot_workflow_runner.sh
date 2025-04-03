#!/bin/bash

# Override the command to run the Discord bot
# This is a more direct approach to avoid port conflicts

# Print a clear message indicating we're bypassing main.py
echo "=========================================================="
echo "      DISCORD BOT WORKFLOW - BYPASSING MAIN.PY"
echo "      RUNNING STANDALONE DISCORD BOT SCRIPT"
echo "=========================================================="

# Execute the clean bot script directly
exec python clean_bot.py
