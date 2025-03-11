import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def get_top_gainers(limit=10):
    """Get top gaining stocks from the market."""
    try:
        # Using yfinance to get S&P 500 tickers
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = sp500['Symbol'].tolist()
        
        gains = []
        for ticker in tickers[:50]:  # Limiting initial scan to first 50 for performance
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Open'].iloc[0]
                    gain = ((current_price - prev_price) / prev_price) * 100
                    gains.append({
                        'ticker': ticker,
                        'gain': gain,
                        'price': current_price,
                        'volume': hist['Volume'].iloc[-1]
                    })
            except Exception:
                continue
        
        # Sort by gain and get top performers
        top_gainers = sorted(gains, key=lambda x: x['gain'], reverse=True)[:limit]
        return top_gainers
    except Exception as e:
        return f"Error fetching top gainers: {str(e)}"

def get_buyer_activity(limit=10):
    """Get stocks with highest buyer activity based on volume and price action."""
    try:
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = sp500['Symbol'].tolist()
        
        buyer_activity = []
        for ticker in tickers[:50]:  # Limiting initial scan
            try:
                stock = yf.Ticker(ticker)
                # Get today's and recent data
                hist = stock.history(period='5d')
                
                if len(hist) >= 5:
                    current_price = hist['Close'].iloc[-1]
                    current_volume = hist['Volume'].iloc[-1]
                    avg_volume = hist['Volume'].mean()
                    
                    # Calculate buying pressure indicators
                    price_range = hist['High'].iloc[-1] - hist['Low'].iloc[-1]
                    close_position = (hist['Close'].iloc[-1] - hist['Low'].iloc[-1]) / price_range if price_range != 0 else 0
                    volume_surge = current_volume / avg_volume
                    
                    # Calculate buy-side pressure
                    # Higher score if:
                    # 1. Price closes near the high (indicating buyer control)
                    # 2. Volume is above average
                    # 3. Price is trending up
                    buying_pressure = (
                        close_position * 50 +  # Position of close in daily range (50% weight)
                        (volume_surge - 1) * 30 +  # Volume surge (30% weight)
                        ((current_price / hist['Close'].iloc[-2] - 1) * 100) * 0.2  # Price trend (20% weight)
                    )
                    
                    buyer_activity.append({
                        'ticker': ticker,
                        'buying_pressure': buying_pressure,
                        'price': current_price,
                        'volume_surge': volume_surge,
                        'close_strength': close_position * 100,
                        'price_change': ((current_price / hist['Close'].iloc[-2] - 1) * 100)
                    })
            except Exception:
                continue
        
        # Sort by buying pressure
        top_buyers = sorted(buyer_activity, key=lambda x: x['buying_pressure'], reverse=True)[:limit]
        return top_buyers
    except Exception as e:
        return f"Error fetching buyer activity: {str(e)}"

def get_momentum_stocks(limit=10):
    """Get stocks with highest intraday momentum compared to previous close."""
    try:
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = sp500['Symbol'].tolist()
        
        momentum_stocks = []
        for ticker in tickers[:50]:  # Limiting initial scan
            try:
                stock = yf.Ticker(ticker)
                # Get today's and yesterday's data
                hist = stock.history(period='2d')
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    current_volume = hist['Volume'].iloc[-1]
                    avg_volume = hist['Volume'].mean()
                    
                    # Calculate momentum indicators
                    price_change = ((current_price - prev_close) / prev_close) * 100
                    volume_ratio = current_volume / avg_volume
                    
                    # Momentum score combines price movement and volume
                    momentum_score = (
                        price_change * 0.7 +  # Price momentum (70% weight)
                        (volume_ratio - 1) * 30  # Volume momentum (30% weight)
                    )
                    
                    momentum_stocks.append({
                        'ticker': ticker,
                        'momentum_score': momentum_score,
                        'price': current_price,
                        'price_change': price_change,
                        'volume_ratio': volume_ratio
                    })
            except Exception:
                continue
        
        # Sort by momentum score
        top_momentum = sorted(momentum_stocks, key=lambda x: x['momentum_score'], reverse=True)[:limit]
        return top_momentum
    except Exception as e:
        return f"Error fetching momentum stocks: {str(e)}"

def format_watchlist_message(stocks, title, type='gainers'):
    """Format the watchlist message for Discord."""
    message = f"📊 **{title}**\n\n"
    
    for i, stock in enumerate(stocks, 1):
        if type == 'gainers':
            message += (f"{i}. ${stock['ticker']}\n"
                       f"   • Gain: {stock['gain']:.2f}%\n"
                       f"   • Price: ${stock['price']:.2f}\n"
                       f"   • Volume: {stock['volume']:,.0f}\n\n")
        elif type == 'buyers':
            message += (f"{i}. ${stock['ticker']}\n"
                       f"   • Buying Pressure: {stock['buying_pressure']:.2f}\n"
                       f"   • Price Change: {stock['price_change']:.2f}%\n"
                       f"   • Volume Surge: {stock['volume_surge']:.1f}x\n"
                       f"   • Close Strength: {stock['close_strength']:.1f}%\n"
                       f"   • Price: ${stock['price']:.2f}\n\n")
        else:  # momentum
            message += (f"{i}. ${stock['ticker']}\n"
                       f"   • Daily Change: {stock['price_change']:.2f}%\n"
                       f"   • Volume vs Avg: {stock['volume_ratio']:.1f}x\n"
                       f"   • Momentum Score: {stock['momentum_score']:.2f}\n"
                       f"   • Price: ${stock['price']:.2f}\n\n")
    
    return message 