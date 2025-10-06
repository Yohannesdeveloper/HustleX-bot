#!/usr/bin/env python3
"""
Direct bot runner - runs the bot directly for testing
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Run the bot directly"""
    logger.info("🤖 Starting HustleX Bot Direct Mode")
    logger.info("=" * 50)
    
    # Check token
    token = os.environ.get("BOT_TOKEN")
    if not token or token == "your_bot_token_here":
        logger.error("❌ BOT_TOKEN not configured!")
        logger.error("Please run: .\configure_bot_token.ps1")
        return 1
    
    logger.info(f"✅ Using token: {token[:10]}...")
    
    try:
        # Import and run the bot
        from bot.main import main as bot_main
        logger.info("🚀 Starting bot...")
        bot_main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


