import os
import logging
import threading
from app import app
from web_scraper import scrape_and_store_program_data
import routes  # noqa: F401

logger = logging.getLogger(__name__)

def initialize_data():
    """Initialize the database with scraped program data"""
    try:
        with app.app_context():
            scrape_and_store_program_data()
            logger.info("Program data scraped and stored successfully")
    except Exception as e:
        logger.error(f"Error initializing data: {e}")

# Initialize data on startup
initialize_data()

logger.info("Flask web application initialized. To start Telegram bot, run: python run_bot.py")
