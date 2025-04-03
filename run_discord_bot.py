#!/usr/bin/env python3
"""
Special entry point for the run_discord_bot workflow.
This script bypasses main.py and directly runs the Discord bot without Flask components.
"""

import os
import sys
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discord_bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Print clear indication that we're running the dedicated Discord bot script
print("="*80)
print(f"DEDICATED DISCORD BOT SCRIPT - {__file__}")
print("NO FLASK COMPONENTS OR PORT CONFLICTS")
print("="*80)

try:
    # Use os.execv to replace the current process with clean_bot.py
    # This completely avoids any Flask imports or port conflicts
    standalone_script = os.path.join(os.path.dirname(__file__), "clean_bot.py")
    logger.info(f"Executing standalone bot script: {standalone_script}")
    os.execv(sys.executable, [sys.executable, standalone_script])
except Exception as e:
    logger.critical(f"Failed to execute clean_bot.py: {e}")
    sys.exit(1)