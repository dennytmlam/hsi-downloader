import csv
import io
import logging
from datetime import datetime
from config import *

logger = logging.getLogger(__name__)

class HSIParser:
    def __init__(self):
        self.columns = []
    
    def parse(self, csv_content, target_date):
        """Parse CSV content and extract all columns
        
        HSI daily report CSV contains:
        - UTF-16 encoded file with BOM
        - Two header rows: Chinese and English
        - Multiple index rows (HSI main + sector indices + USD version)
        
        Columns (13 total):
        Trade Date, Index, Index Currency, Daily High, Daily Low,
        Index Close, Point Change, % Change, Dividend Yield (%),
        PE Ratio (times), Index Turnover (Mn), Market Turnover (Mn),
        Index Currency to HKD
        """
        # Detect and handle UTF-16 encoding
        decoded_content = self._decode_utf16(csv_content)
        
        # Split into lines (handle both CRLF and LF)
        lines = decoded_content.strip().replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        # Skip Chinese header (line 0), use English header (line 1) as fieldnames
        # Lines 2+ are data rows
        if len(lines) < 2:
            raise ValueError("CSV file must have at least 2 header rows")
        
        # Get English column headers from second row
        self.columns = lines[1].split('\t')
        # Remove quotes and whitespace from column names
        self.columns = [col.strip().strip('"') for col in self.columns]
        
        logger.info(f"Detected columns: {self.columns}")
        
        # Parse data rows (skip both header rows)
        rows = []
        for line in lines[2:]:
            if line.strip():
                values = line.split('\t')
                # Remove quotes and whitespace from values
                values = [v.strip().strip('"') for v in values]
                # Create dict row
                row = dict(zip(self.columns, values))
                rows.append(row)
        
        logger.info(f"Parsed {len(rows)} rows")
        return rows, self.columns
    
    def _decode_utf16(self, csv_bytes):
        """Decode UTF-16 encoded CSV content"""
        # Try UTF-16 first (HSI files are UTF-16 LE with BOM)
        try:
            # Remove BOM if present and decode
            if csv_bytes.startswith(b'\xff\xfe'):
                return csv_bytes[2:].decode('utf-16-le')
            elif csv_bytes.startswith(b'\xfe\xff'):
                return csv_bytes[2:].decode('utf-16-be')
            else:
                return csv_bytes.decode('utf-16')
        except UnicodeDecodeError:
            # Fallback to UTF-8
            return csv_bytes.decode('utf-8')
    
    def normalize_columns(self, row, expected_columns):
        """Ensure all rows have the same columns"""
        normalized = {}
        for col in expected_columns:
            normalized[col] = row.get(col, '')
        return normalized
