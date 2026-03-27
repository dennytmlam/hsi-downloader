#!/usr/bin/env python3
"""
Send HSI chart to Telegram
"""

import os
from notifier import HSINotifier

def main():
    notifier = HSINotifier()
    
    # Read the chart
    chart_file = "downloads/hsi_daily_report.txt"
    
    if not os.path.exists(chart_file):
        print(f"Error: {chart_file} not found")
        return
    
    with open(chart_file, 'r', encoding='utf-8') as f:
        chart_content = f.read()
    
    # Send as plain text (no markdown parsing issues)
    message = "📊 HSI Daily Report\n\nGenerated: 26 Mar 2026 15:28\nData Date: 27 Feb 2026\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nClose: 26,630.54\nRSI (14): 51.7 NEUTRAL\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nPrice Chart (last 20 days):\n\n" + chart_content
    
    print("Sending HSI chart to Telegram...")
    result = notifier.send_error_notification(message)
    
    if result:
        print("✅ Chart sent successfully to Telegram!")
    else:
        print("❌ Failed to send chart")
        print(f"Chat ID: {notifier.chat_id}")
        print(f"Bot token set: {bool(notifier.bot_token)}")

if __name__ == "__main__":
    main()
