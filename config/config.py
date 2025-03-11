import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
APCA_API_KEY_ID = os.getenv('ALPACA_API_KEY')
APCA_API_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Trading Parameters
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Risk Management
MAX_POSITION_SIZE = 0.1  # Maximum position size as a fraction of portfolio
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.05  # 5% take profit

# Market Data
DEFAULT_TIMEFRAME = "1d"
DEFAULT_PERIOD = "1y"

# Technical Analysis Parameters
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30 