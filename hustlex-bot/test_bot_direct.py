#!/usr/bin/env python3
"""
Direct bot test script to verify the bot works properly
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

def test_bot_token():
    """Test if bot token is properly configured"""
    token = os.environ.get("BOT_TOKEN")
    
    if not token:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        return False
    
    if token == "your_bot_token_here":
        logger.error("❌ BOT_TOKEN is still set to placeholder value!")
        logger.error("Please set a real Telegram bot token.")
        return False
    
    if len(token) < 40:
        logger.error("❌ BOT_TOKEN appears to be invalid (too short)")
        return False
    
    logger.info("✅ BOT_TOKEN is configured")
    return True

def test_imports():
    """Test if all required modules can be imported"""
    try:
        from telegram import Bot
        from telegram.ext import ApplicationBuilder
        logger.info("✅ Telegram library imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import telegram library: {e}")
        return False

async def test_bot_connection():
    """Test connection to Telegram API"""
    try:
        from telegram import Bot
        token = os.environ.get("BOT_TOKEN")
        
        if not token or token == "your_bot_token_here":
            logger.error("❌ Cannot test connection without valid token")
            return False
        
        bot = Bot(token=token)
        # This will raise an exception if the token is invalid
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot connected successfully: @{bot_info.username}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Telegram: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🤖 Testing HustleX Bot Configuration")
    logger.info("=" * 50)
    
    tests = [
        ("Token Configuration", test_bot_token),
        ("Library Imports", test_imports),
        ("Telegram Connection", lambda: __import__('asyncio').run(test_bot_connection()))
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Testing: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Bot is ready to run.")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
