import requests
import time
import os
import logging
from datetime import datetime, timedelta
from config import *

logger = logging.getLogger(__name__)

class HSIDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Ensure downloads directory exists
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    def generate_date_urls(self, target_days_ago=None):
        """
        Generate URLs for target date and fallback dates.
        
        HSI only publishes previous day's data:
        - On March 25th, only March 24th's data is available
        - Default: target_days_ago = 1 (yesterday)
        - Fallback: try older dates if target not found
        """
        if target_days_ago is None:
            target_days_ago = DEFAULT_TARGET_DAYS_AGO
        
        urls = []
        # Start from target date, go back up to DATE_TOLERANCE_DAYS
        for days_ago in range(target_days_ago, target_days_ago + DATE_TOLERANCE_DAYS):
            date = datetime.now() - timedelta(days=days_ago)
            date_str = format_hsi_date(date)
            url = HSI_BASE_URL.format(date=date_str)
            urls.append((url, date))
        return urls
    
    def download(self, target_days_ago=None):
        """
        Download HSI data for specified day.
        
        Args:
            target_days_ago: Days before today (default: 1 for yesterday)
        
        Returns:
            (csv_content, target_date, saved_file_path) tuple
        
        Note: HSI only publishes previous day's data.
        On March 25th, only March 24th's data is available.
        """
        urls = self.generate_date_urls(target_days_ago)
        
        for url, target_date in urls:
            for attempt in range(MAX_RETRIES):
                try:
                    logger.info(f"Attempting to download {target_date.strftime('%d %b %Y')} data from {url} (attempt {attempt + 1})")
                    response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    
                    if response.content.strip():  # Non-empty response
                        # Save raw file to downloads directory
                        filename = f"idx_{format_hsi_date(target_date)}.csv"
                        saved_path = os.path.join(DOWNLOADS_DIR, filename)
                        
                        with open(saved_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"Successfully downloaded {target_date.strftime('%d %b %Y')} data from {url}")
                        logger.info(f"Saved raw file to: {saved_path}")
                        
                        return response.content, target_date, saved_path
                    
                except requests.RequestException as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {target_date.strftime('%d %b %Y')}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
        
        raise Exception(f"Failed to download HSI data for past {DATE_TOLERANCE_DAYS} days after all retries")
