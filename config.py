import os

# required token for Telegram API
TELEGRAM_BOT_KEY = os.environ.get("TELEGRAM_BOT_KEY")
# prometheus exporter port
METRICS_PORT = int(os.getenv('METRICS_PORT', 5000))
# if it is winter, some commands will be disabled to use
IS_WINTER = bool(os.getenv('IS_WINTER', False))

API_ADDRESS = os.getenv("API_ADDRESS", "https://agropogoda.com/api")
MONITOR_API_ADDRESS = os.getenv("MONITOR_API_ADDRESS", "https://monitor.agropogoda.com/api")

CONVERSATION_DUMP_FILE = os.getenv("CONVERSATION_DUMP_FILE", "conversationbot")

