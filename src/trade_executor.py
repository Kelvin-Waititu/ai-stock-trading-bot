import alpaca_trade_api as tradeapi
from config.config import APCA_API_KEY_ID, APCA_API_SECRET_KEY, MAX_POSITION_SIZE

# Initialize Alpaca API
api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, "https://paper-api.alpaca.markets")

def get_account_info():
    """Get account information and positions."""
    try:
        account = api.get_account()
        positions = api.list_positions()
        return {
            'cash': float(account.cash),
            'portfolio_value': float(account.portfolio_value),
            'positions': positions
        }
    except Exception as e:
        raise Exception(f"Error fetching account info: {str(e)}")

def execute_trade(ticker, action, quantity=None):
    """Executes a buy or sell order using Alpaca API."""
    try:
        # Validate action
        if action.lower() not in ['buy', 'sell']:
            return "❌ Invalid action. Use 'buy' or 'sell'."

        # Use default quantity if not specified
        if quantity is None:
            quantity = DEFAULT_QUANTITY

        # Get current position
        positions = api.list_positions()
        current_position = next((p for p in positions if p.symbol == ticker), None)

        # Validate sell order
        if action.lower() == 'sell':
            if not current_position:
                return f"❌ No position found for {ticker}"
            if int(quantity) > int(current_position.qty):
                return f"❌ Insufficient shares. You have {current_position.qty} shares of {ticker}"

        # Get current price and account info
        current_price = float(api.get_latest_bar(ticker).c)
        order_value = current_price * int(quantity)
        account = api.get_account()
        portfolio_value = float(account.portfolio_value)
        max_position_value = portfolio_value * MAX_POSITION_SIZE

        # Validate buy order
        if action.lower() == 'buy':
            if order_value > float(account.cash):
                return f"❌ Insufficient funds. Required: ${order_value:.2f}, Available: ${float(account.cash):.2f}"
            if order_value > max_position_value:
                return f"❌ Order value (${order_value:.2f}) exceeds maximum position size (${max_position_value:.2f})"

        # Submit order
        order = api.submit_order(
            symbol=ticker,
            qty=int(quantity),
            side=action.lower(),
            type="market",
            time_in_force="gtc"
        )

        return f"✅ {action.upper()} order placed for {quantity} shares of {ticker} at ${current_price:.2f}"

    except Exception as e:
        return f"❌ Trade execution failed: {str(e)}"

def get_position(ticker):
    """Get current position for a specific ticker."""
    try:
        positions = api.list_positions()
        position = next((p for p in positions if p.symbol == ticker), None)
        if position:
            return {
                'symbol': position.symbol,
                'quantity': int(position.qty),
                'avg_entry_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'market_value': float(position.market_value),
                'unrealized_pl': float(position.unrealized_pl)
            }
        return None
    except Exception as e:
        raise Exception(f"Error fetching position: {str(e)}") 