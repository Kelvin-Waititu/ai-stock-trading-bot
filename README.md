# AI Stock Trading Bot 🤖📈

An intelligent trading bot that uses AI to analyze stocks, execute trades, and provide real-time market insights through Discord.

## Contributors 👥

- **Kelvin Waititu** - Core Developer
- **Stephen Makuol** - Core Developer

## Features 🌟

- AI-powered trading decisions using Google's Gemini model
- Real-time market analysis and sentiment tracking
- Automated trade execution through Alpaca Markets
- Discord bot interface for easy interaction
- Top gainers and momentum stock tracking
- Buying pressure analysis
- Portfolio management and position tracking

## Prerequisites 📋

- Python 3.8+
- Discord account
- Alpaca Markets account
- Google Cloud account (for Gemini API)

## Getting API Tokens 🔑

Before setting up the bot, you'll need to obtain the following API tokens:

1. **Alpaca Markets API Keys**:

   - Go to [Alpaca Markets](https://alpaca.markets/)
   - Sign up for a free account
   - Choose between paper trading (recommended for testing) or live trading
   - Navigate to Dashboard -> API Keys
   - Copy your API Key ID and Secret Key

2. **Discord Bot Token**:

   - Visit the [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Go to the "Bot" section and click "Add Bot"
   - Click "Reset Token" and copy your bot token
   - Under "Privileged Gateway Intents", enable "Message Content Intent"
   - Use the OAuth2 URL Generator to invite the bot to your server:
     - Select "bot" under scopes
     - Select required permissions (Send Messages, Read Messages, etc.)
     - Copy and open the generated URL to invite the bot

3. **Google API Key (for Gemini)**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gemini API for your project
   - Go to APIs & Services -> Credentials
   - Click "Create Credentials" -> "API Key"
   - Copy your API key

## Installation 🔧

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ai-stock-trading-bot.git
cd ai-stock-trading-bot
```

2. Install dependencies:

```bash
pip install -r deployment/requirements.txt
```

3. Create a `.env` file in the root directory with your API tokens:

```env
APCA_API_KEY_ID=your_alpaca_api_key
APCA_API_SECRET_KEY=your_alpaca_secret_key
DISCORD_TOKEN=your_discord_bot_token
GOOGLE_API_KEY=your_google_api_key
```

## Rate Limits and Quotas ⚡

The bot implements several measures to handle API rate limits and quotas:

### Discord Commands

- `!trade` command has a 30-second cooldown per user
- Progress messages show when analysis is in progress
- Cooldowns are reset on errors for retry attempts

### Gemini API Rate Limiting

- Minimum 2-second delay between consecutive API calls
- Exponential backoff with jitter for retries:
  - Starts with 1-second delay
  - Doubles after each failure (up to 32 seconds)
  - Random jitter added to prevent synchronized retries
  - Maximum 5 retry attempts
- Request timeout set to 30 seconds
- Automatic error handling and recovery

### Quota Management Tips

1. Monitor your API usage in Google Cloud Console
2. Consider upgrading to paid tier for higher quotas
3. Use the paper trading environment for testing
4. Implement additional delays during high-traffic periods

## Usage 💡

Start the bot:

```bash
python src/bot.py
```

### Discord Commands

- `!start` - Display welcome message and available commands
- `!trade <TICKER>` - Get AI analysis for a stock
- `!buy <TICKER> <QUANTITY>` - Buy shares
- `!sell <TICKER> <QUANTITY>` - Sell shares
- `!position <TICKER>` - Check position details
- `!account` - View account information
- `!gainers` - View top gaining stocks
- `!momentum` - View high momentum stocks
- `!buyers` - View stocks with strong buying activity

## Project Structure 📁

```
ai-stock-trading-bot/
├── src/
│   ├── bot.py              # Discord bot implementation
│   ├── ai_trader.py        # AI analysis and trading logic
│   ├── trade_executor.py   # Trade execution handling
│   ├── market_data.py      # Market data fetching
│   └── watchlist.py        # Stock watchlist functionality
├── config/
│   └── config.py           # Configuration settings
├── deployment/
│   └── requirements.txt    # Project dependencies
└── .env                    # API tokens and secrets
```

## Dependencies 📦

- discord.py - Discord bot framework
- alpaca-trade-api - Trading API
- yfinance - Market data
- langchain - AI framework
- google-generativeai - Gemini AI model
- pandas & numpy - Data processing
- python-dotenv - Environment management


## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer ⚠️

This bot is for educational purposes only. Trading stocks carries risk, and you should never trade with money you cannot afford to lose. The creators are not responsible for any financial losses incurred while using this bot.
