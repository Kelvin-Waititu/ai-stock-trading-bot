import discord
from discord.ext import commands
from market_data import get_technical_indicators, get_stock_info
from ai_trader import analyze_sentiment, ai_trading_decision, generate_trade_summary
from trade_executor import execute_trade, get_account_info, get_position
from watchlist import (
    get_top_gainers,
    get_momentum_stocks,
    get_buyer_activity,
    format_watchlist_message,
)
from config.config import DISCORD_TOKEN
import asyncio
from datetime import datetime, timedelta

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Command cooldown tracking
last_trade_time = {}
TRADE_COOLDOWN = 30  # seconds between trades per user


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!help for commands"))


@bot.command(name="start")
async def start(ctx):
    """Start a conversation with the bot."""
    welcome_msg = (
        "👋 Hey there! Want to trade today? 🚀\n"
        "**Use these commands to get started:**\n"
        "🔹 `!trade <TICKER>` → Get AI insights on a stock (30s cooldown)\n"
        "🔹 `!buy <TICKER> <QUANTITY>` → Buy shares\n"
        "🔹 `!sell <TICKER> <QUANTITY>` → Sell shares\n"
        "🔹 `!position <TICKER>` → Check your position\n"
        "🔹 `!account` → View account info\n"
        "🔹 `!gainers` → View top gaining stocks\n"
        "🔹 `!momentum` → View high momentum stocks\n"
        "🔹 `!buyers` → View stocks with strong buying activity\n"
        "🔹 `!help` → See all commands"
    )
    await ctx.send(welcome_msg)


@bot.command(name="trade")
async def trade(ctx, ticker: str):
    """Get AI-powered trade insights for a stock."""
    user_id = ctx.author.id
    current_time = datetime.now()

    # Check cooldown
    if user_id in last_trade_time:
        time_since_last = (current_time - last_trade_time[user_id]).total_seconds()
        if time_since_last < TRADE_COOLDOWN:
            remaining = int(TRADE_COOLDOWN - time_since_last)
            await ctx.send(
                f"⏳ Please wait {remaining} seconds before requesting another trade analysis."
            )
            return

    try:
        # Update last trade time
        last_trade_time[user_id] = current_time

        # Send acknowledgment
        await ctx.send(f"🔄 Analyzing {ticker}... Please wait.")

        # Get stock data
        technical_data = get_technical_indicators(ticker)
        stock_info = get_stock_info(ticker)

        # Get news sentiment with delay
        news_sentiment = analyze_sentiment(f"Recent news about {ticker}")
        await asyncio.sleep(2)  # Add small delay between API calls

        # Get AI trading decision
        decision = ai_trading_decision(ticker, technical_data, news_sentiment)

        # Generate summary
        summary = generate_trade_summary(ticker, decision, technical_data)

        # Add stock info
        summary += f"""
📈 Stock Information:
   • Name: {stock_info['name']}
   • Sector: {stock_info['sector']}
   • Industry: {stock_info['industry']}
   • Market Cap: ${stock_info['market_cap']:,.2f}
   • P/E Ratio: {stock_info['pe_ratio']}
   • Dividend Yield: {stock_info['dividend_yield']}
"""

        await ctx.send(summary)
    except Exception as e:
        await ctx.send(f"❌ Error analyzing {ticker}: {str(e)}")
        # Reset cooldown on error
        if user_id in last_trade_time:
            del last_trade_time[user_id]


@bot.command(name="buy")
async def buy(ctx, ticker: str, quantity: int = None):
    """Buy shares of a stock."""
    try:
        response = execute_trade(ticker, "buy", quantity)
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"❌ Error executing buy order: {str(e)}")


@bot.command(name="sell")
async def sell(ctx, ticker: str, quantity: int = None):
    """Sell shares of a stock."""
    try:
        response = execute_trade(ticker, "sell", quantity)
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"❌ Error executing sell order: {str(e)}")


@bot.command(name="position")
async def position(ctx, ticker: str):
    """Check your position in a stock."""
    try:
        position = get_position(ticker)
        if position:
            msg = f"""
📊 **Position in {ticker}**
   • Quantity: {position['quantity']} shares
   • Average Entry: ${position['avg_entry_price']:.2f}
   • Current Price: ${position['current_price']:.2f}
   • Market Value: ${position['market_value']:.2f}
   • Unrealized P/L: ${position['unrealized_pl']:.2f}
"""
        else:
            msg = f"No position found for {ticker}"
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"❌ Error fetching position: {str(e)}")


@bot.command(name="account")
async def account(ctx):
    """View account information."""
    try:
        info = get_account_info()
        msg = f"""
💰 **Account Information**
   • Cash: ${info['cash']:.2f}
   • Portfolio Value: ${info['portfolio_value']:.2f}
   • Number of Positions: {len(info['positions'])}
"""
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"❌ Error fetching account info: {str(e)}")


@bot.command(name="gainers")
async def gainers(ctx, limit: int = 10):
    """Get top gaining stocks."""
    try:
        await ctx.send("🔍 Scanning market for top gainers...")
        top_gainers = get_top_gainers(limit)
        if isinstance(top_gainers, str):  # Error message
            await ctx.send(f"❌ {top_gainers}")
        else:
            message = format_watchlist_message(
                top_gainers, "Today's Top Gainers 📈", "gainers"
            )
            await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Error fetching top gainers: {str(e)}")


@bot.command(name="momentum")
async def momentum(ctx, limit: int = 10):
    """Get stocks with highest daily momentum."""
    try:
        await ctx.send("🔍 Scanning market for momentum stocks...")
        momentum_stocks = get_momentum_stocks(limit)
        if isinstance(momentum_stocks, str):  # Error message
            await ctx.send(f"❌ {momentum_stocks}")
        else:
            message = format_watchlist_message(
                momentum_stocks, "Today's Top Momentum Stocks 🚀", "momentum"
            )
            await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Error fetching momentum stocks: {str(e)}")


@bot.command(name="buyers")
async def buyers(ctx, limit: int = 10):
    """Get stocks with highest buyer activity."""
    try:
        await ctx.send("🔍 Scanning market for stocks with strong buying activity...")
        buyer_stocks = get_buyer_activity(limit)
        if isinstance(buyer_stocks, str):  # Error message
            await ctx.send(f"❌ {buyer_stocks}")
        else:
            message = format_watchlist_message(
                buyer_stocks, "Stocks with Strong Buying Activity 💪", "buyers"
            )
            await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Error fetching buyer activity: {str(e)}")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use !help to see command usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument. Use !help to see command usage.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")


# Run the bot
bot.run(DISCORD_TOKEN)
