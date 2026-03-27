#!/usr/bin/env python3
"""
Create HSI chart as PNG image using basic PIL
"""

import csv
import os
from datetime import datetime
from config import *

def calculate_rsi(prices, period=14):
    """Calculate RSI from price list"""
    if len(prices) < period + 1:
        return None
    
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [max(0, c) for c in changes]
    losses = [abs(min(0, c)) for c in changes]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def extract_hsi_closes(csv_file, index_name="Hang Seng Index 恒生指數"):
    """Extract closing prices for main HSI"""
    closes = []
    dates = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Index', '') == index_name:
                try:
                    close = float(row.get('Index Close', 0))
                    date_str = row.get('Trade Date', '')
                    if close > 0 and date_str:
                        closes.append(close)
                        dates.append(date_str)
                except (ValueError, TypeError):
                    continue
    
    return dates, closes

def create_simple_chart(dates, closes, rsi_values, output_file):
    """Create a simple chart using basic file operations"""
    
    # Get latest data
    latest_date = dates[-1]
    latest_close = closes[-1]
    latest_rsi = rsi_values[-1] if rsi_values else None
    
    # Create text report
    lines = []
    lines.append("=" * 70)
    lines.append("                    HSI DAILY REPORT")
    lines.append("=" * 70)
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  Data Date: {latest_date}")
    lines.append("")
    lines.append("  Close Price:  {:,.2f}".format(latest_close))
    
    if latest_rsi:
        if latest_rsi < 30:
            status = "🟢 OVERSOLD (Buy Signal)"
        elif latest_rsi > 70:
            status = "🔴 OVERBOUGHT (Sell Signal)"
        else:
            status = "🟡 NEUTRAL"
        lines.append("  RSI (14):     {:.1f}  {}".format(latest_rsi, status))
    
    lines.append("")
    lines.append("-" * 70)
    lines.append("  PRICE CHART (Last 20 Trading Days)")
    lines.append("-" * 70)
    
    # Create price chart
    recent_closes = closes[-20:]
    recent_dates = dates[-20:]
    
    min_price = min(recent_closes)
    max_price = max(recent_closes)
    price_range = max_price - min_price if max_price != min_price else 1
    
    chart_height = 15
    
    for row in range(chart_height, -1, -1):
        threshold = min_price + (price_range * row / chart_height)
        
        if row == chart_height:
            line = f"  {threshold:,.0f}"
        elif row == 0:
            line = f"  {threshold:,.0f}"
        else:
            line = f"  {' ':8}"
        
        for price in recent_closes:
            if price >= threshold - (price_range / chart_height / 2):
                line += "█"
            else:
                line += " "
        
        if row == 0:
            line += f"  {recent_closes[-1]:,.0f}"
        
        lines.append(line)
    
    lines.append("   " + "└" + "─" * len(recent_closes) + "┘")
    
    # Add date labels
    label_spacing = max(1, len(recent_dates) // 10)
    date_labels = "   "
    for i, d in enumerate(recent_dates):
        if i % label_spacing == 0:
            date_labels += d[6:] + " "
        else:
            date_labels += "  "
    lines.append(date_labels)
    
    lines.append("")
    lines.append("-" * 70)
    lines.append("  SECTOR RSI COMPARISON")
    lines.append("-" * 70)
    
    # Add sector data placeholder
    lines.append("  (Sector analysis coming soon)")
    lines.append("")
    lines.append("=" * 70)
    lines.append("  Source: hsi.com.hk | Total days in database: {}".format(len(dates)))
    lines.append("=" * 70)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print('\n'.join(lines))
    return output_file

def main():
    csv_file = os.path.join(DATA_DIR, "hsi_data.csv")
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found")
        return
    
    print("📊 Generating HSI Chart...")
    print("")
    
    dates, closes = extract_hsi_closes(csv_file)
    
    if len(closes) < 15:
        print(f"❌ Not enough data: {len(closes)} days (need at least 15 for RSI)")
        return
    
    print(f"✅ Found {len(dates)} trading days")
    
    # Calculate RSI
    rsi_values = []
    for i in range(14, len(closes)):
        rsi = calculate_rsi(closes[:i+1], 14)
        rsi_values.append(rsi if rsi else 50.0)
    
    # Generate chart
    chart_file = os.path.join(DOWNLOADS_DIR, "hsi_daily_report.txt")
    create_simple_chart(dates, closes, rsi_values, chart_file)
    
    print("")
    print(f"✅ Chart saved to: {chart_file}")

if __name__ == "__main__":
    main()
