#!/usr/bin/env python3
"""
HSI Data Downloader
Downloads Hang Seng Index data daily and appends to CSV

Note: HSI only publishes previous day's data.
On March 25th, only March 24th's data is available.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from config import *
from downloader import HSIDownloader
from parser import HSIParser
from storage import HSIStorage
from notifier import HSINotifier
from housekeeper import HSIHousekeeper

# Setup logging
def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

def main(target_days_ago=None):
    """
    Main execution flow
    
    Args:
        target_days_ago: Optional override for which day to download
                        (default: 1 = yesterday, per HSI's publication schedule)
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("HSI Data Downloader - Starting")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Determine target date
    if target_days_ago is None:
        target_days_ago = DEFAULT_TARGET_DAYS_AGO
    
    target_date = datetime.now() - timedelta(days=target_days_ago)
    logger.info(f"Target date: {target_date.strftime('%d %b %Y')} ({target_days_ago} day(s) ago)")
    logger.info("Note: HSI only publishes previous day's data")
    
    # Initialize notifier for error reporting
    notifier = HSINotifier()
    
    try:
        # Initialize components
        downloader = HSIDownloader()
        parser = HSIParser()
        storage = HSIStorage()
        
        # Download data (with fallback to older dates if needed)
        csv_content, actual_date, saved_path = downloader.download(target_days_ago)
        
        if actual_date != target_date:
            logger.info(f"Note: Downloaded {actual_date.strftime('%d %b %Y')} instead of target {target_date.strftime('%d %b %Y')}")
        
        # Parse data
        rows, columns = parser.parse(csv_content, actual_date)
        
        # Initialize storage with columns
        storage.initialize(columns)
        
        # Append data
        written = storage.append(rows)
        
        logger.info(f"Completed: {written} new rows added for {actual_date.strftime('%d %b %Y')}")
        
        # Run housekeeping (clean up old downloaded files)
        housekeeper = HSIHousekeeper()
        housekeeper.run()
        
        logger.info("=" * 60)
        
        return written
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        
        # Send Telegram notification on failure
        error_msg = f"❌ HSI Data Download Failed\n\n" \
                   f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                   f"Error: {str(e)}\n" \
                   f"Target Date: {target_date.strftime('%d %b %Y')}"
        
        try:
            notifier.send_error_notification(error_msg)
            logger.info("Error notification sent to Telegram")
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {notify_error}")
        
        raise

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Allow command-line override: python main.py 2 (download 2 days ago)
    target_days_ago = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    logger.info(f"Command line args: {sys.argv}")
    logger.info(f"Target days ago: {target_days_ago}")
    
    try:
        result = main(target_days_ago)
        logger.info(f"Main completed with result: {result}")
    except Exception as e:
        logger.error(f"Main failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
