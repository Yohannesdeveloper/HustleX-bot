#!/usr/bin/env python3
"""
Quick test to verify the bot is working live
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot_live():
    """Test if the bot is actually working"""
    try:
        from telegram import Bot
        
        token = os.environ.get("BOT_TOKEN")
        if not token:
            print("ERROR: No BOT_TOKEN found")
            return False
        
        print(f"Testing bot with token: {token[:10]}...")
        
        bot = Bot(token=token)
        bot_info = await bot.get_me()
        
        print(f"SUCCESS: Bot is LIVE and working!")
        print(f"Bot Name: {bot_info.first_name}")
        print(f"Username: @{bot_info.username}")
        print(f"Bot ID: {bot_info.id}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Bot test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing HustleX Bot Live Status")
    print("=" * 40)
    
    success = asyncio.run(test_bot_live())
    
    if success:
        print("\nSUCCESS: Your bot is LIVE and ready to receive messages!")
        print("Try sending /start to your bot in Telegram")
    else:
        print("\nERROR: Bot is not working. Check the token and configuration.")
    
    sys.exit(0 if success else 1)
