import requests
import logging
import json
import os
from config import *

logger = logging.getLogger(__name__)

class HSINotifier:
    """
    Telegram notification module for HSI data downloader.
    
    Sends error notifications to Telegram when the downloader fails.
    Uses the existing OpenClaw Telegram bot configuration.
    """
    
    def __init__(self):
        self.enabled = TELEGRAM_ENABLED
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Try to load from OpenClaw config if not set
        if not self.bot_token:
            self.bot_token = self._load_bot_token_from_openclaw_config()
        
        if self.enabled and not self.bot_token:
            logger.warning("Telegram notifications enabled but BOT_TOKEN not set")
            self.enabled = False
        
        if self.enabled and not self.chat_id:
            # Try to load chat ID from OpenClaw config as fallback
            self.chat_id = self._load_chat_id_from_openclaw_config()
        
        if self.enabled and not self.chat_id:
            logger.warning("Telegram notifications enabled but CHAT_ID not set")
            self.enabled = False
    
    def _load_bot_token_from_openclaw_config(self):
        """Load Telegram bot token from OpenClaw config"""
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            bot_token = config.get('channels', {}).get('telegram', {}).get('accounts', {}).get('default', {}).get('botToken', '')
            
            if bot_token:
                logger.info("Loaded Telegram bot token from OpenClaw config")
                return bot_token
        except (OSError, json.JSONDecodeError) as e:
            logger.debug(f"Could not load OpenClaw config: {e}")
        
        return ""
    
    def _load_chat_id_from_openclaw_config(self):
        """Load Telegram chat ID from OpenClaw config (first enabled group)"""
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            groups = config.get('channels', {}).get('telegram', {}).get('accounts', {}).get('default', {}).get('groups', {})
            
            # Find first enabled group
            for chat_id, settings in groups.items():
                if settings.get('enabled', False):
                    logger.info(f"Loaded Telegram chat ID from OpenClaw config: {chat_id}")
                    return chat_id
        except (OSError, json.JSONDecodeError) as e:
            logger.debug(f"Could not load OpenClaw config: {e}")
        
        return ""
    
    def send_error_notification(self, error_message):
        """
        Send error notification to Telegram.
        
        Args:
            error_message: String message to send
        """
        if not self.enabled:
            logger.info("Telegram notifications disabled")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": error_message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            if response.json().get("ok"):
                logger.info("Telegram error notification sent successfully")
                return True
            else:
                logger.error(f"Telegram API returned error: {response.json()}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
    def send_success_notification(self, message):
        """
        Send success notification to Telegram (optional).
        
        Args:
            message: String message to send
        """
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": f"✅ {message}",
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            return response.json().get("ok", False)
            
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram success notification: {e}")
            return False
    
    def test_connection(self):
        """
        Test Telegram connection and configuration.
        
        Returns:
            bool: True if connection test successful
        """
        if not self.enabled:
            return False
        
        test_message = "🔔 <b>HSI Downloader Test</b>\n\nTelegram notification is working!"
        return self.send_error_notification(test_message)
