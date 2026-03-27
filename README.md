# HSI Data Downloader

Automated Hang Seng Index data downloader with Telegram notifications and automatic housekeeping.

## Features

- ✅ Downloads daily HSI data from hsi.com.hk
- ✅ Handles UTF-16 encoded CSV files
- ✅ Stores 13 columns of index data (main HSI + sector indices)
- ✅ Organized folder structure (data/, downloads/, logs/)
- ✅ **Telegram error notifications** when downloads fail
- ✅ **Automatic housekeeping** - cleans up files older than 30 days
- ✅ Deduplication using composite key (Trade Date + Index)
- ✅ Configurable retention period and notification settings

## Quick Start

### 1. Install Dependencies

```bash
cd hsi-downloader
pip install -r requirements.txt
```

### 2. Configure Telegram Notifications (Optional)

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Or edit `config.py` directly.

### 3. Run Manually

```bash
# Download yesterday's data (default)
python main.py

# Download specific day's data
python main.py 2    # 2 days ago
python main.py 3    # 3 days ago
```

### 4. Set Up Automatic Daily Run

**Option A: Cron Job (Linux/Mac)**
```bash
crontab -e
# Add this line (runs daily at 8:00 AM HK time):
0 8 * * * /usr/bin/python3 /path/to/hsi-downloader/main.py >> /path/to/hsi-downloader/logs/cron.log 2>&1
```

**Option B: OpenClaw Cron**
Ask your OpenClaw agent to create a cron job with:
```json
{
  "name": "HSI Data Download",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Hong_Kong"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "Run HSI data downloader: cd /path/to/hsi-downloader && python main.py"
  },
  "sessionTarget": "isolated"
}
```

## Folder Structure

```
hsi-downloader/
├── data/              # Persistent combined data (hsi_data.csv)
├── downloads/         # Raw downloaded files (auto-cleaned after 30 days)
├── logs/             # Log files
└── [source files]
```

## Configuration

Edit `config.py` to customize:

- `DOWNLOAD_RETENTION_DAYS`: How long to keep raw files (default: 30)
- `HOUSEKEEPING_ENABLED`: Enable/disable auto-cleanup (default: True)
- `TELEGRAM_ENABLED`: Enable/disable notifications (default: True)
- `DEFAULT_TARGET_DAYS_AGO`: Which day to download (default: 1 = yesterday)

## Telegram Setup Guide

The HSI downloader can automatically use your existing OpenClaw Telegram bot!

### Option A: Use Existing OpenClaw Bot (Recommended)

The downloader will automatically load the bot token from your OpenClaw config (`~/.openclaw/openclaw.json`).

**All you need to do is set your Chat ID:**

```bash
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

**To find your Chat ID:**
1. Message any Telegram bot (e.g., @userinfobot)
2. Or visit: `https://api.telegram.org/bot<EXISTING_BOT_TOKEN>/getUpdates`
3. Copy the `chat_id` from the response

**No need to create a new bot!** The downloader uses your existing OpenClaw bot.

### Option B: Use a Different Bot

If you want to use a separate bot for HSI notifications:

1. **Create Bot:** Message @BotFather → `/newbot` → copy token
2. **Get Chat ID:** Message your bot → visit `https://api.telegram.org/bot<TOKEN>/getUpdates` → find `chat_id`
3. **Configure:** Set both environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   ```

### Test the Connection

```bash
cd hsi-downloader
python -c "from notifier import HSINotifier; HSINotifier().test_connection()"
```

You should receive a test message on Telegram!

## Data Columns

The HSI daily report contains 13 columns:

| Column | Description |
|--------|-------------|
| Trade Date | YYYYMMDD format |
| Index | Index name (bilingual) |
| Index Currency | HKD/USD |
| Daily High | Highest value |
| Daily Low | Lowest value |
| Index Close | Closing value |
| Point Change | Point change |
| % Change | Percentage change |
| Dividend Yield (%) | Dividend yield |
| PE Ratio (times) | P/E ratio |
| Index Turnover (Mn) | Index turnover in millions |
| Market Turnover (Mn) | Market turnover in millions |
| Index Currency to HKD | Exchange rate |

## Monitoring

```bash
# View logs
tail -f logs/hsi_downloader.log

# View data
tail -20 data/hsi_data.csv

# Check housekeeping stats
python -c "from housekeeper import HSIHousekeeper; print(HSIHousekeeper().get_stats())"
```

## Important Notes

- HSI only publishes **previous day's** data
- On March 25th, only March 24th's data is available
- Files are UTF-16 encoded with BOM
- Each date has 6 rows (main HSI + 4 sectors + USD version)
