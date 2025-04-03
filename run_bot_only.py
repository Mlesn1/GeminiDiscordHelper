#!/usr/bin/env python3
"""
Special script to run only the Discord bot without Flask.
This sets the environment variable to make main.py run in Discord bot only mode.
"""
import os
import sys
import logging
import subprocess

# Set the environment variable before importing other modules
os.environ["REPL_WORKFLOW_NAME"] = "run_discord_bot"

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Run the Discord bot only using main.py."""
    logger.info("Starting Discord bot only (no web server)...")
    
    try:
        # Run main.py with the environment variable set
        result = subprocess.run([sys.executable, "main.py"], 
                              env=dict(os.environ, REPL_WORKFLOW_NAME="run_discord_bot"),
                              check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run Discord bot: {e}")
        return e.returncode
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())