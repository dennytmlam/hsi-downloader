# HSI Data Downloader - Design Document

## Overview

A Python script that:
1. Downloads **previous day's** HSI (Hang Seng Index) data from HSI website
2. Extracts all columns from the CSV
3. Appends new data to a persistent CSV file
4. Runs automatically every day

**Important:** HSI only publishes previous day's data. On March 25th, only March 24th's data is available.

## Architecture

```
hsi-downloader/
├── main.py                 # Main script with error handling & notifications
├── backfill.py             # Historical data backfill script
├── config.py               # Configuration settings
├── downloader.py           # Download logic (saves raw files)
├── parser.py               # CSV parsing and extraction
├── storage.py              # Data persistence
├── notifier.py             # Telegram error notifications
├── housekeeper.py          # Cleanup old files (>30 days)
├── requirements.txt        # Dependencies
├── data/                   # Persistent data storage
│   └── hsi_data.csv       # Combined historical data
├── downloads/              # Raw downloaded files (auto-cleaned)
│   └── idx_*.csv          # Original HSI files
└── logs/                   # Log files
    └── hsi_downloader.log
```

## Components

### 1. Configuration (`config.py`)

```python
# HSI Data Downloader Configuration

# Source URL (date will be substituted)
HSI_BASE_URL = "https://www.hsi.com.hk/static/uploads/contents/en/indexes/report/hsi/idx_{date}.csv"

# Date format in filename (DMMMYY - no zero padding for day)
# HSI uses: 2Mar26 not 02Mar26
def format_hsi_date(date):
    """Format date for HSI filename (no zero-padding on day)"""
    return date.strftime("%-d%b%y")  # %-d removes zero padding on Linux

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")           # For persistent data files
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads") # For raw downloaded files
LOGS_DIR = os.path.join(BASE_DIR, "logs")           # For log files

# Output file path (persistent combined data)
OUTPUT_CSV = os.path.join(DATA_DIR, "hsi_data.csv")

# Log file path
LOG_FILE = os.path.join(LOGS_DIR, "hsi_downloader.log")

# Request settings
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Date handling
# HSI only publishes previous day's data
# On March 25th, only March 24th's data is available
DEFAULT_TARGET_DAYS_AGO = 1  # Download yesterday's data by default
DATE_TOLERANCE_DAYS = 3  # Fallback: try up to 3 days back if yesterday missing

# Expected columns in HSI daily report CSV
# Based on actual data from hsi.com.hk (13 columns, English headers)
EXPECTED_COLUMNS = [
    "Trade Date",              # YYYYMMDD format
    "Index",                   # Index name (bilingual)
    "Index Currency",          # HKD or USD
    "Daily High",              # Highest value
    "Daily Low",               # Lowest value
    "Index Close",             # Closing value
    "Point Change",            # Point change
    "% Change",                # Percentage change
    "Dividend Yield (%)",      # Dividend yield
    "PE Ratio (times)",        # P/E ratio
    "Index Turnover (Mn)",     # Index turnover in millions
    "Market Turnover (Mn)",    # Market turnover in millions
    "Index Currency to HKD"    # Exchange rate to HKD
]

# File encoding
FILE_ENCODING = "utf-16"  # HSI files are UTF-16 LE with BOM

# Housekeeping settings
HOUSEKEEPING_ENABLED = True
DOWNLOAD_RETENTION_DAYS = 30  # Keep downloaded raw files for 30 days

# Telegram notification settings
TELEGRAM_ENABLED = True
# Bot token and chat ID can be set via environment variables:
# export TELEGRAM_BOT_TOKEN="your_bot_token_here"
# export TELEGRAM_CHAT_ID="your_chat_id_here"
# If not set, will automatically load from OpenClaw config (~/.openclaw/openclaw.json)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
```

### 2. Downloader (`downloader.py`)

```python
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
        
        Date format: HSI uses no zero-padding (2Mar26 not 02Mar26)
        """
        if target_days_ago is None:
            target_days_ago = DEFAULT_TARGET_DAYS_AGO
        
        urls = []
        # Start from target date, go back up to DATE_TOLERANCE_DAYS
        for days_ago in range(target_days_ago, target_days_ago + DATE_TOLERANCE_DAYS):
            date = datetime.now() - timedelta(days=days_ago)
            date_str = format_hsi_date(date)  # Use no-zero-padding format
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
```

### 3. Parser (`parser.py`)

```python
import csv
import io
from datetime import datetime
from config import *

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
        
        # Read CSV
        reader = csv.DictReader(io.StringIO(decoded_content))
        
        # Get column headers (use English row - second row)
        # Skip Chinese header row, use English header row
        self.columns = reader.fieldnames
        logger.info(f"Detected columns: {self.columns}")
        
        # Parse all rows
        rows = []
        for row in reader:
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
```

## HSI Daily Report Columns

Based on the actual HSI daily report CSV file (`idx_20Mar26.csv`), the data contains the following characteristics:

### File Format
- **Encoding**: UTF-16 LE with BOM (`\xff\xfe`)
- **Headers**: Two rows - Chinese headers first, then English headers
- **Data**: Multiple index rows per date (main HSI + sector indices + USD version)

### Columns (13 total)

| # | English Column Name | Chinese Column Name | Description | Example |
|---|---------------------|---------------------|-------------|---------|
| 1 | `Trade Date` | `交易日` | Trading date (YYYYMMDD format) | 20260320 |
| 2 | `Index` | `指數` | Index name (bilingual) | Hang Seng Index 恒生指數 |
| 3 | `Index Currency` | `指數貨幣` | Currency denomination | HKD / USD |
| 4 | `Daily High` | `全日最高` | Highest index value during the day | 25563.88 |
| 5 | `Daily Low` | `全日最低` | Lowest index value during the day | 25121.46 |
| 6 | `Index Close` | `指數收市` | Closing index value | 25277.32 |
| 7 | `Point Change` | `點數變動` | Point change from previous close | -223.26 |
| 8 | `% Change` | `百分比變動` | Percentage change from previous close | -0.88 |
| 9 | `Dividend Yield (%)` | `股息率` | Dividend yield percentage | 3.04 |
| 10 | `PE Ratio (times)` | `市盈率` | Price-to-earnings ratio | 13.34 |
| 11 | `Index Turnover (Mn)` | `指數成交額 (百萬元)` | Index trading volume in millions | 152100 |
| 12 | `Market Turnover (Mn)` | `市場成交額 (百萬元)` | Total market trading volume in millions | 342518 |
| 13 | `Index Currency to HKD` | `指數貨幣兌港元匯率` | Exchange rate to HKD | 1 (or 7.83745 for USD) |

### Index Types in File

Each date has multiple rows for different indices:
1. **Hang Seng Index 恒生指數** (main HSI in HKD)
2. **Hang Seng Index - Finance 恒生金融分類指數** (Finance sector)
3. **Hang Seng Index - Utilities 恒生公用事業分類指數** (Utilities sector)
4. **Hang Seng Index - Properties 恒生地產分類指數** (Properties sector)
5. **Hang Seng Index - Commerce & Industry 恒生工商業分類指數** (Commerce & Industry sector)
6. **Hang Seng Index USD 恒生指數美元** (main HSI in USD)

**Note:** The parser must handle UTF-16 encoding and skip the Chinese header row to use English column names.

### 4. Storage (`storage.py`)

```python
import csv
import os
from datetime import datetime
from config import *

class HSIStorage:
    def __init__(self):
        self.output_file = OUTPUT_CSV
        self.columns = []
    
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
```

### 5. Main Script (`main.py`)

```python
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
from datetime import datetime
from config import *
from downloader import HSIDownloader
from parser import HSIParser
from storage import HSIStorage

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
    
    try:
        # Initialize components
        downloader = HSIDownloader()
        parser = HSIParser()
        storage = HSIStorage()
        
        # Download data (with fallback to older dates if needed)
        csv_content, actual_date = downloader.download(target_days_ago)
        
        if actual_date != target_date:
            logger.info(f"Note: Downloaded {actual_date.strftime('%d %b %Y')} instead of target {target_date.strftime('%d %b %Y')}")
        
        # Parse data
        rows, columns = parser.parse(csv_content, actual_date)
        
        # Initialize storage with columns
        storage.initialize(columns)
        
        # Append data
        written = storage.append(rows)
        
        logger.info(f"Completed: {written} new rows added for {actual_date.strftime('%d %b %Y')}")
        logger.info("=" * 60)
        
        return written
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    setup_logging()
    
    # Allow command-line override: python main.py 2 (download 2 days ago)
    target_days_ago = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    try:
        main(target_days_ago)
    except Exception as e:
        sys.exit(1)
```

### 6. Backfill Script (`backfill.py`)

```python
#!/usr/bin/env python3
"""
Backfill HSI data for historical dates

Usage:
    python backfill.py <start_date> [end_date]
    
Example:
    python backfill.py 2026-03-02 2026-03-09
    python backfill.py 2026-02-01  # Download up to yesterday
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
```

**Features:**
- Downloads historical data for any date range
- Skips weekends automatically (HKEX doesn't trade)
- Handles holidays (skips dates where data isn't available)
- Deduplicates data (won't add rows that already exist)
- Runs housekeeping after completion

### 7. Requirements (`requirements.txt`)

```
requests>=2.28.0
```

## Scheduling Options

### Option A: Cron Job (Linux/Mac)

```bash
# Run daily at 8:00 AM
0 8 * * * /usr/bin/python3 /path/to/hsi-downloader/main.py >> /path/to/hsi-downloader/logs/cron.log 2>&1
```

### Option B: Windows Task Scheduler

```powershell
# Create scheduled task (run daily at 8:00 AM)
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "/path/to/hsi-downloader/main.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -TaskName "HSI Data Download" -Action $action -Trigger $trigger
```

### Option C: OpenClaw Cron (Recommended)

```python
# Add to OpenClaw cron jobs
{
  "name": "HSI Data Download",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Hong_Kong"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "Run HSI data downloader script"
  },
  "sessionTarget": "isolated"
}
```

## Data Flow

```
┌─────────────────┐
│  HSI Website    │
│  idx_DDMMMYY.csv│
└────────┬────────┘
         │ Download
         ▼
┌─────────────────┐
│  CSV Content    │
│  (raw bytes)    │
└────────┬────────┘
         │ Parse
         ▼
┌─────────────────┐
│  Structured     │
│  Data (rows)    │
└────────┬────────┘
         │ Append
         ▼
┌─────────────────┐
│  hsi_data.csv   │
│  (persistent)   │
└─────────────────┘
```

## Error Handling

1. **Network failures**: Retry up to 3 times with 5-second delays
2. **Missing files**: Try recent dates (within 2 days)
3. **Duplicate data**: Skip rows with existing dates
4. **Column changes**: Automatically add new columns to existing CSV
5. **Empty responses**: Skip and retry

## Logging

All operations logged to `logs/hsi_downloader.log`:
- Download attempts and results
- Parse statistics (rows, columns)
- Append operations (new rows added)
- Errors and exceptions

## Usage

### Daily Download

```bash
# Download yesterday's data (default, recommended for daily cron)
python main.py

# Download specific day's data (for catch-up or testing)
python main.py 2    # 2 days ago
python main.py 3    # 3 days ago

# Install as cron job (runs daily at 8:00 AM)
crontab -e
# Add: 0 8 * * * /usr/bin/python3 /path/to/main.py >> /path/to/hsi-downloader/logs/cron.log 2>&1

# Check logs
tail -f logs/hsi_downloader.log

# View accumulated data
tail -20 hsi_data.csv
```

### Historical Backfill

```bash
# Download data for a specific date range
python backfill.py 2026-03-02 2026-03-09

# Download from a start date up to yesterday (default end date)
python backfill.py 2026-02-01

# Download entire month
python backfill.py 2026-02-01 2026-02-28

# Download multiple months
python backfill.py 2026-01-01 2026-03-01
```

**Important notes:**
- HSI only publishes previous day's data for recent dates
- Historical data availability depends on HSI's archive policy
- The backfill script skips weekends and handles missing dates gracefully
- Date format in URLs: HSI uses no zero-padding (`2Mar26` not `02Mar26`)

## Future Enhancements

- [ ] Add data validation (check for expected values)
- [x] Add email/telegram notifications on failure
- [x] Add historical data backfill script
- [ ] Add data backup (daily snapshots)
- [ ] Add statistics dashboard
- [ ] Support multiple index types
- [ ] Add data cleaning (handle special characters)

## Telegram Notifications

The downloader sends error notifications to Telegram when failures occur.

### Setup - Uses Your Existing OpenClaw Bot!

The HSI downloader automatically loads the Telegram bot token from your OpenClaw configuration (`~/.openclaw/openclaw.json`).

**All you need to do:**

1. **Find your Chat ID:**
   - Message @userinfobot on Telegram, or
   - Visit: `https://api.telegram.org/bot<EXISTING_TOKEN>/getUpdates`
   - Copy the `chat_id` from the response

2. **Set your Chat ID:**
   ```bash
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   ```

That's it! The bot token is loaded automatically from OpenClaw.

### Alternative: Use Environment Variables

You can also set both manually:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or edit `config.py` directly.

### Error Notification Format

```
❌ HSI Data Download Failed

Time: 2026-03-25 22:30:00
Error: Failed to download HSI data for past 3 days after all retries
Target Date: 24 Mar 2026
```

### Test Connection

```bash
cd hsi-downloader
python -c "from notifier import HSINotifier; HSINotifier().test_connection()"
```

## Housekeeping

Automatically cleans up old downloaded raw files to save disk space.

### Configuration

- **Retention Period:** 30 days (configurable in `config.py`)
- **Target Directory:** `downloads/`
- **Enabled:** Yes (set `HOUSEKEEPING_ENABLED = False` to disable)

### How It Works

1. Every run checks the `downloads/` directory
2. Files older than 30 days (by modification time) are deleted
3. Cleanup statistics are logged:
   ```
   Running housekeeping: cleaning files older than 30 days
   Housekeeping complete: deleted 5 files, freed 12.5 KB
   ```

### Manual Cleanup

```python
from housekeeper import HSIHousekeeper

housekeeper = HSIHousekeeper()
stats = housekeeper.run()
print(f"Deleted {stats['files_deleted']} files, freed {stats['space_freed']}")
```

### View Current Stats

```python
from housekeeper import HSIHousekeeper

housekeeper = HSIHousekeeper()
stats = housekeeper.get_stats()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size']}")
print(f"Oldest: {stats['oldest_file']} ({stats['oldest_file_date']})")
print(f"Newest: {stats['newest_file']} ({stats['newest_file_date']})")
```
