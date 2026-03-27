#!/usr/bin/env python3
"""
Backfill HSI data for historical dates
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from config import *
from downloader import HSIDownloader
from parser import HSIParser
from storage import HSIStorage
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

def backfill_date(target_date):
    """Download data for a specific date"""
    logger = logging.getLogger(__name__)
    
    # Calculate days ago
    days_ago = (datetime.now() - target_date).days
    
    logger.info(f"Attempting to download data for {target_date.strftime('%Y-%m-%d')} ({days_ago} days ago)")
    
    try:
        # Initialize components
        downloader = HSIDownloader()
        parser = HSIParser()
        storage = HSIStorage()
        
        # Download data
        csv_content, actual_date, saved_path = downloader.download(days_ago)
        
        # Parse data
        rows, columns = parser.parse(csv_content, actual_date)
        
        # Initialize storage with columns
        storage.initialize(columns)
        
        # Append data
        written = storage.append(rows)
        
        logger.info(f"✓ Downloaded {written} rows for {actual_date.strftime('%Y-%m-%d')}")
        return written
        
    except Exception as e:
        logger.warning(f"✗ Failed to download {target_date.strftime('%Y-%m-%d')}: {e}")
        return 0

def main(start_date_str, end_date_str=None):
    """
    Backfill HSI data for a date range
    
    Args:
        start_date_str: Start date in YYYY-MM-DD format
        end_date_str: End date in YYYY-MM-DD format (default: yesterday)
    """
    logger = logging.getLogger(__name__)
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else datetime.now() - timedelta(days=1)
    
    logger.info("=" * 60)
    logger.info(f"HSI Data Backfill")
    logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info("=" * 60)
    
    total_rows = 0
    dates_attempted = 0
    
    # Iterate through dates
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends (HSI doesn't trade on weekends)
        if current_date.weekday() < 5:  # 0=Monday, 4=Friday
            dates_attempted += 1
            rows = backfill_date(current_date)
            total_rows += rows
        
        current_date += timedelta(days=1)
    
    logger.info("=" * 60)
    logger.info(f"Backfill complete: {total_rows} rows added from {dates_attempted} trading days")
    logger.info("=" * 60)
    
    # Run housekeeping
    housekeeper = HSIHousekeeper()
    housekeeper.run()
    
    return total_rows

if __name__ == "__main__":
    setup_logging()
    
    if len(sys.argv) < 2:
        print("Usage: python backfill.py <start_date> [end_date]")
        print("Example: python backfill.py 2026-03-02 2026-03-09")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = main(start_date, end_date)
    except Exception as e:
        logging.error(f"Backfill failed: {e}")
        sys.exit(1)
