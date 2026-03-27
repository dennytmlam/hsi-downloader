# HSI Data Downloader Configuration

import os

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
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1001003884427758")  # HSI channel (negative for channels)
