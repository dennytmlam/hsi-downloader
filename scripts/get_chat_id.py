#!/usr/bin/env python3
"""
Get the chat ID from forwarded messages to the bot
Run this after forwarding a message from your group/channel to @Assistant_Nate_Bot
"""

import requests
import json

bot_token = "8681255897:AAFjheic21YNQAilBmRZgqAcAxIWtC1TcuM"

print("🔍 Checking for recent messages...")
print("👉 Forward a message from your HSI group/channel to @Assistant_Nate_Bot")
print("   Then run this script again\n")

url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    updates = response.json().get("result", [])
    
    if updates:
        print(f"Found {len(updates)} recent update(s):\n")
        
        for i, update in enumerate(updates, 1):
            message = update.get("message", {})
            chat = message.get("chat", {})
            
            chat_id = chat.get("id")
            chat_type = chat.get("type")
            chat_title = chat.get("title", "N/A")
            
            print(f"{i}. Chat ID: {chat_id}")
            print(f"   Type: {chat_type}")
            print(f"   Name: {chat_title}")
            
            # Check if it's from a group/channel
            if chat_type in ["group", "supergroup", "channel"]:
                print(f"   ⭐ This looks like your HSI group/channel!")
                print(f"   👉 Use this ID: {chat_id}")
            print()
    else:
        print("No recent messages found.")
        print("👉 Forward a message from your group to @Assistant_Nate_Bot first")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
