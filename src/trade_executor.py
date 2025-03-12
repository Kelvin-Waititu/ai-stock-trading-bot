import alpaca_trade_api as tradeapi
from config.config import APCA_API_KEY_ID, APCA_API_SECRET_KEY, MAX_POSITION_SIZE
import time

# Initialize Alpaca API
api = tradeapi.REST(
    APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url="https://paper-api.alpaca.markets"
)


def get_current_price(symbol):
    """Get current price of a stock."""
    try:
        bars = api.get_latest_bar(symbol)
        return bars.c
    except Exception as e:
        raise Exception(f"Error fetching price for {symbol}: {str(e)}")


def check_day_trade_count():
    """Check number of day trades in the last 5 trading days."""
    account = api.get_account()
    return int(account.daytrade_count)


def wait_for_order_fill(order_id, timeout=60):
    """Wait for an order to be filled."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        order = api.get_order(order_id)
        if order.status == "filled":
            return True
        elif order.status == "rejected":
            raise Exception(f"Order rejected: {order.failed_at}")
        time.sleep(1)
    return False


def execute_trade(symbol, side, quantity=None):
    """Execute a trade with complex order handling."""
    try:
        # Get account information
        account = api.get_account()
        buying_power = float(account.buying_power)
        portfolio_value = float(account.portfolio_value)
        max_trade_value = portfolio_value * MAX_POSITION_SIZE

        # Get current position if exists
        try:
            position = api.get_position(symbol)
            current_position_qty = int(position.qty)
            current_position_value = float(position.market_value)
        except Exception:
            current_position_qty = 0
            current_position_value = 0

        # Get current price
        current_price = get_current_price(symbol)

        if side == "buy":
            # Calculate quantity if not provided
            if quantity is None:
                max_shares = int(max_trade_value / current_price)
                quantity = min(max_shares, int(buying_power / current_price))
                if quantity <= 0:
                    return (
                        "❌ Insufficient buying power or maximum position size reached."
                    )

            # Check if this would exceed maximum position size
            total_position_value = (current_position_qty + quantity) * current_price
            if total_position_value > max_trade_value:
                quantity = int(
                    (max_trade_value - current_position_value) / current_price
                )
                if quantity <= 0:
                    return "❌ Maximum position size would be exceeded."

            # Place buy order
            order = api.submit_order(
                symbol=symbol,
                qty=quantity,
                side="buy",
                type="market",
                time_in_force="gtc",
                order_class="simple",
            )

        else:  # sell
            if current_position_qty <= 0:
                return "❌ No position to sell."

            # Use provided quantity or sell entire position
            quantity = quantity if quantity else current_position_qty
            if quantity > current_position_qty:
                return f"❌ Cannot sell {quantity} shares, only have {current_position_qty}."

            # Calculate take profit and stop loss prices
            take_profit_price = round(current_price * 1.02, 2)  # 2% above current price
            stop_loss_price = round(current_price * 0.98, 2)  # 2% below current price

            # Place bracket order for selling
            order = api.submit_order(
                symbol=symbol,
                qty=quantity,
                side="sell",
                type="limit",
                time_in_force="gtc",
                limit_price=current_price,
                order_class="bracket",
                take_profit={"limit_price": take_profit_price},
                stop_loss={
                    "stop_price": stop_loss_price,
                    "limit_price": stop_loss_price,
                },
            )

        # Wait for order fill
        if wait_for_order_fill(order.id):
            filled_order = api.get_order(order.id)
            filled_price = float(filled_order.filled_avg_price)
            total_value = filled_price * quantity
            return (
                f"✅ {side.upper()} order filled:\n"
                f"   • Symbol: {symbol}\n"
                f"   • Quantity: {quantity} shares\n"
                f"   • Price: ${filled_price:.2f}\n"
                f"   • Total Value: ${total_value:.2f}"
            )
        else:
            api.cancel_order(order.id)
            return f"❌ Order timeout - cancelled after 60 seconds."

    except Exception as e:
        error_msg = str(e)
        if "wash trade" in error_msg.lower():
            return (
                "❌ Trade rejected: To avoid wash trade, try:\n"
                "1. Selling a different quantity\n"
                "2. Waiting a few minutes between trades\n"
                "3. Using a limit price slightly different from market price"
            )
        return f"❌ Trade execution failed: {str(e)}"


def get_position(symbol):
    """Get current position information."""
    try:
        position = api.get_position(symbol)
        return {
            "quantity": int(position.qty),
            "avg_entry_price": float(position.avg_entry_price),
            "current_price": float(position.current_price),
            "market_value": float(position.market_value),
            "unrealized_pl": float(position.unrealized_pl),
        }
    except Exception:
        return None


def get_account_info():
    """Get account information."""
    try:
        account = api.get_account()
        positions = api.list_positions()
        return {
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "positions": positions,
        }
    except Exception as e:
        raise Exception(f"Error fetching account info: {str(e)}")
