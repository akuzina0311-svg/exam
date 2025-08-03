#!/usr/bin/env python3
"""
Separate script to run the Telegram bot
This runs independently from the Flask web application
"""
import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from app import app
from telegram_bot import setup_bot, run_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Telegram bot"""
    logger.info("Starting ITMO AI Programs Telegram Bot...")
    
    # Check if bot token is available
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or token == "your-bot-token-here":
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        logger.error("Please set the bot token in Replit Secrets")
        return
    
    try:
        # Setup and run bot with Flask app context
        with app.app_context():
            bot = setup_bot()
            logger.info("Bot setup complete, starting polling...")
            run_bot(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

if __name__ == "__main__":
    main()