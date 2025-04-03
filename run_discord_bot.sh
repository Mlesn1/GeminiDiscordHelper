#!/bin/bash

# This script is used by the run_discord_bot workflow
# It sets a specific environment variable to ensure our detection code works

echo "=========================================================="
echo "      STARTING DISCORD BOT WITH ENVIRONMENT FLAG"
echo "      This script sets DISCORD_BOT_WORKFLOW_ONLY=1"
echo "=========================================================="

# Set the environment variable that our detection code looks for
export DISCORD_BOT_WORKFLOW_ONLY=1

# Execute main.py with the environment variable set
# This should trigger our early detection code
python main.py
