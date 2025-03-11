import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL

def get_stock_data(ticker, period="1d", interval="1m"):
    """Fetch stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        return df
    except Exception as e:
        raise Exception(f"Error fetching data for {ticker}: {str(e)}")

def calculate_rsi(data):
    """Calculate RSI indicator."""
    rsi_indicator = RSIIndicator(close=data['Close'], window=RSI_PERIOD)
    return rsi_indicator.rsi().iloc[-1]

def calculate_macd(data):
    """Calculate MACD indicator."""
    macd = MACD(
        close=data['Close'],
        window_slow=MACD_SLOW,
        window_fast=MACD_FAST,
        window_sign=MACD_SIGNAL
    )
    return {
        'macd': macd.macd().iloc[-1],
        'signal': macd.macd_signal().iloc[-1],
        'histogram': macd.macd_diff().iloc[-1]
    }

def get_technical_indicators(ticker):
    """Get all technical indicators for a stock."""
    data = get_stock_data(ticker)
    
    rsi = calculate_rsi(data)
    macd_data = calculate_macd(data)
    
    current_price = data['Close'].iloc[-1]
    
    return {
        'price': current_price,
        'rsi': rsi,
        'macd': macd_data['macd'],
        'macd_signal': macd_data['signal'],
        'macd_hist': macd_data['histogram'],
        'volume': data['Volume'].iloc[-1]
    }

def get_stock_info(ticker):
    """Get basic stock information."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('forwardPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A')
        }
    except Exception as e:
        raise Exception(f"Error fetching info for {ticker}: {str(e)}") 