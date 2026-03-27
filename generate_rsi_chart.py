#!/usr/bin/env python3
"""
Generate HSI RSI chart and send to Telegram
"""

import csv
import os
from datetime import datetime
from config import *
from notifier import HSINotifier

def calculate_rsi(prices, period=14):
    """Calculate RSI from price list"""
    if len(prices) < period + 1:
        return None
    
    # Calculate changes
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [max(0, c) for c in changes]
    losses = [abs(min(0, c)) for c in changes]
    
    # Calculate average gain and loss
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

def generate_ascii_chart(dates, closes, rsi_values, chart_file):
    """Generate ASCII chart"""
    lines = []
    lines.append("📊 HSI Daily Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)
    lines.append("")
    
    # Latest data
    if closes:
        latest_date = dates[-1]
        latest_close = closes[-1]
        latest_rsi = rsi_values[-1] if rsi_values else None
        
        lines.append(f"📅 Date: {latest_date}")
        lines.append(f"💹 Close: {latest_close:,.2f}")
        if latest_rsi:
            rsi_status = "🟢 Oversold" if latest_rsi < 30 else "🔴 Overbought" if latest_rsi > 70 else "🟡 Neutral"
            lines.append(f"📈 RSI(14): {latest_rsi:.1f} {rsi_status}")
        lines.append("")
    
    # Price chart (last 20 days)
    lines.append("📈 Price Movement (Last 20 days)")
    lines.append("-" * 60)
    
    if len(closes) >= 2:
        recent_closes = closes[-20:]
        recent_dates = dates[-20:]
        
        min_price = min(recent_closes)
        max_price = max(recent_closes)
        price_range = max_price - min_price if max_price != min_price else 1
        
        chart_height = 10
        
        # Create chart
        for row in range(chart_height, -1, -1):
            threshold = min_price + (price_range * row / chart_height)
            line = f"{threshold:,.0f} │"
            
            for price in recent_closes:
                if price >= threshold - (price_range / chart_height / 2):
                    line += "█"
                else:
                    line += " "
            line += f" {recent_closes[-1]:,.0f}"
            lines.append(line)
        
        lines.append("     └" + "─" * len(recent_closes) + "─")
        lines.append("      " + " ".join([d[6:] for d in recent_dates[::max(1, len(recent_dates)//10)]]))
    
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"Data source: hsi.com.hk | Total days: {len(dates)}")
    
    # Write to file
    with open(chart_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return '\n'.join(lines)

def main():
    # Extract HSI data
    csv_file = os.path.join(DATA_DIR, "hsi_data.csv")
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found")
        return
    
    print("Extracting HSI data...")
    dates, closes = extract_hsi_closes(csv_file)
    
    if len(closes) < 15:
        print(f"Not enough data: {len(closes)} days (need at least 15 for RSI)")
        return
    
    print(f"Found {len(dates)} trading days")
    
    # Calculate RSI
    print("Calculating RSI...")
    rsi_values = []
    for i in range(14, len(closes)):
        rsi = calculate_rsi(closes[:i+1], 14)
        rsi_values.append(rsi if rsi else 50.0)
    
    # Generate chart
    chart_file = os.path.join(DOWNLOADS_DIR, "hsi_chart.txt")
    print("Generating chart...")
    chart_text = generate_ascii_chart(dates, closes, rsi_values, chart_file)
    
    # Send to Telegram
    print("Sending to Telegram...")
    notifier = HSINotifier()
    
    # Send as document (text file)
    message = f"📊 *HSI Daily Chart*\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\nSee attached chart for price movement and RSI analysis."
    
    try:
        with open(chart_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Send the chart as a message with formatting
        notifier.send_error_notification(message)
        
        # Send the actual chart content
        chart_message = f"```{chart_text}```"
        notifier.send_error_notification(chart_message)
        
        print("✅ Chart sent to Telegram!")
        
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        print(f"\nChart content:\n{chart_text}")

if __name__ == "__main__":
    main()
