import csv
import os
import logging
from datetime import datetime
from config import *

logger = logging.getLogger(__name__)

class HSIStorage:
    def __init__(self):
        self.output_file = OUTPUT_CSV
        self.columns = []
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def initialize(self, columns):
        """Create CSV file with headers if it doesn't exist"""
        self.columns = columns
        
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
            logger.info(f"Created new output file: {self.output_file}")
        else:
            # Verify existing columns
            existing_columns = self._read_existing_columns()
            new_columns = set(columns) - set(existing_columns)
            if new_columns:
                logger.info(f"Adding new columns: {new_columns}")
                self._add_columns(new_columns)
                self.columns = existing_columns + list(new_columns)
    
    def append(self, rows):
        """Append rows to CSV, avoiding duplicates
        
        Uses composite key: Trade Date + Index name
        """
        existing_keys = self._get_existing_keys()
        
        new_rows = []
        for row in rows:
            key = (row.get('Trade Date', ''), row.get('Index', ''))
            if key not in existing_keys:
                new_rows.append(row)
                existing_keys.add(key)
        
        if not new_rows:
            logger.info("No new data to append (already exists)")
            return 0
        
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            written = 0
            for row in new_rows:
                normalized = {col: row.get(col, '') for col in self.columns}
                writer.writerow(normalized)
                written += 1
        
        logger.info(f"Appended {written} new rows to {self.output_file}")
        return written
    
    def _read_existing_columns(self):
        """Read existing column headers from file"""
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            return next(reader)
    
    def _get_existing_keys(self):
        """Get set of (Trade Date, Index) tuples already in the file"""
        keys = set()
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get('Trade Date', ''), row.get('Index', ''))
                keys.add(key)
        return keys
    
    def _add_columns(self, new_columns):
        """Add new columns to existing CSV"""
        # Read all existing data
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            existing_columns = reader.fieldnames
        
        # Rewrite with new columns
        all_columns = existing_columns + list(new_columns)
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns)
            writer.writeheader()
            for row in rows:
                normalized = {col: row.get(col, '') for col in all_columns}
                writer.writerow(normalized)
