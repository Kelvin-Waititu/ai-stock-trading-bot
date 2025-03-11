import time
import random
from functools import wraps
from typing import Any, Callable
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import GOOGLE_API_KEY

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the model with a lower temperature for more focused responses
model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.7,
    convert_system_message_to_human=True,
    max_retries=3,  # Limit retries
    request_timeout=30,  # Set timeout
)

# Rate limiting settings
MIN_DELAY_BETWEEN_CALLS = 2.0  # Minimum seconds between API calls
last_api_call_time = 0


def wait_for_rate_limit():
    """Ensure minimum delay between API calls."""
    global last_api_call_time
    current_time = time.time()
    time_since_last_call = current_time - last_api_call_time

    if time_since_last_call < MIN_DELAY_BETWEEN_CALLS:
        sleep_time = MIN_DELAY_BETWEEN_CALLS - time_since_last_call
        time.sleep(sleep_time)

    last_api_call_time = time.time()


class RateLimitError(Exception):
    """Custom exception for rate limiting"""

    pass


def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 32.0,
    jitter: bool = True,
) -> Callable:
    """
    Decorator for exponential backoff with jitter.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter: Whether to add random jitter to delay
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e) or "Resource has been exhausted" in str(e):
                        retries += 1
                        if retries == max_retries:
                            raise RateLimitError(
                                f"Maximum retries ({max_retries}) exceeded. Last error: {str(e)}"
                            )

                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2 ** (retries - 1)), max_delay)

                        # Add jitter if enabled
                        if jitter:
                            delay = delay * (0.5 + random.random())

                        print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                    else:
                        raise
            return None

        return wrapper

    return decorator


@exponential_backoff()
def analyze_sentiment(query: str) -> str:
    """Analyze market sentiment with rate limiting and retries."""
    try:
        wait_for_rate_limit()  # Add rate limiting

        prompt = f"""
        Analyze the market sentiment for: {query}
        
        Please provide a structured analysis covering:
        1. Overall market sentiment (bullish/bearish/neutral)
        2. Key factors influencing the sentiment
        3. Potential market impact
        
        Keep the response concise and focused on actionable insights.
        """

        response = model.invoke(prompt)
        return response.content
    except Exception as e:
        if "429" in str(e):
            raise  # Let the decorator handle rate limiting
        return f"Error analyzing sentiment: {str(e)}"


@exponential_backoff()
def ai_trading_decision(ticker: str, technical_data: dict, sentiment: str) -> str:
    """Generate trading decision with rate limiting and retries."""
    try:
        wait_for_rate_limit()  # Add rate limiting

        prompt = f"""
        Analyze {ticker} for trading decision based on:
        
        Technical Indicators:
        {technical_data}
        
        Market Sentiment:
        {sentiment}
        
        Provide:
        1. Trading recommendation (Buy/Sell/Hold)
        2. Confidence level (1-10)
        3. Key reasons for decision
        4. Risk factors to consider
        5. Suggested entry/exit points
        
        Keep the analysis focused and actionable.
        """

        response = model.invoke(prompt)
        return response.content
    except Exception as e:
        if "429" in str(e):
            raise  # Let the decorator handle rate limiting
        return f"Error generating trading decision: {str(e)}"


def generate_trade_summary(ticker: str, decision: str, technical_data: dict) -> str:
    """Format the trading decision into a Discord message."""
    try:
        summary = f"""
🎯 **Trading Analysis for ${ticker}**

{decision}

📊 **Technical Indicators**
"""
        # Add key technical indicators
        for indicator, value in technical_data.items():
            if isinstance(value, (int, float)):
                summary += f"• {indicator}: {value:.2f}\n"
            else:
                summary += f"• {indicator}: {value}\n"

        return summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def truncate_message(message, max_length=1500):
    """Truncate message to fit Discord's limit."""
    if len(message) <= max_length:
        return message
    return message[: max_length - 3] + "..."


def analyze_sentiment(news_headline):
    """Uses LLM to analyze stock news sentiment."""
    try:
        prompt = f"""
        Quick sentiment analysis:
        {news_headline}
        
        Format: Sentiment (pos/neg/neu) - Key impact
        """
        response = model.invoke(prompt)
        return truncate_message(response.content)
    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"


def ai_trading_decision(ticker, technical_data, news_sentiment):
    """Uses an AI model to decide whether to buy/sell."""
    try:
        prompt = f"""
        Quick trading analysis for {ticker}:
        Price: ${technical_data['price']:.2f}
        RSI: {technical_data['rsi']:.2f}
        MACD: {technical_data['macd']:.2f}
        News: {news_sentiment}

        Format: Action (Buy/Sell/Hold) - Confidence% - Key reason
        """

        response = model.invoke(prompt)
        return truncate_message(response.content)
    except Exception as e:
        return f"Error generating trading decision: {str(e)}"


def generate_trade_summary(ticker, decision, technical_data):
    """Generate a formatted summary of the trading decision."""
    summary = f"""
📊 {ticker} Analysis
💰 ${technical_data['price']:.2f} | RSI: {technical_data['rsi']:.2f}
🤖 {decision}
"""
    return truncate_message(summary)
