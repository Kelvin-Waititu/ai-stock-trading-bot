import alpaca_trade_api as tradeapi
from config.config import APCA_API_KEY_ID, APCA_API_SECRET_KEY, MAX_POSITION_SIZE
import time

# Initialize Alpaca API
api = tradeapi.REST(
    APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url="https://paper-api.alpaca.markets"
)


def get_current_price(symbol, side="buy"):
    """Get current price of a stock."""
    try:
        quote = api.get_latest_quote(symbol)
        # Use ask price for buying, bid price for selling
        return float(quote.ask_price) if side == "buy" else float(quote.bid_price)
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
    """Execute a trade with simple market orders."""
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

        # Get current price based on side
        current_price = get_current_price(symbol, side)

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

        else:  # sell
            if current_position_qty <= 0:
                return "❌ No position to sell."

            # Use provided quantity or sell entire position
            quantity = quantity if quantity else current_position_qty
            if quantity > current_position_qty:
                return f"❌ Cannot sell {quantity} shares, only have {current_position_qty}."

        # Try to place the order
        try:
            # Set limit price slightly above ask for buy or below bid for sell to ensure fill
            limit_price = round(current_price * (1.001 if side == "buy" else 0.999), 2)

            # Submit limit order
            order = api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type="limit",
                time_in_force="day",
                limit_price=limit_price,
                extended_hours=True,
            )

            # Short wait for fill
            time.sleep(1)

            # Check order status
            filled_order = api.get_order(order.id)
            if filled_order.status == "filled":
                filled_price = float(filled_order.filled_avg_price)
                filled_qty = float(filled_order.filled_qty)
                total_value = filled_price * filled_qty
                return (
                    f"✅ {side.upper()} order filled:\n"
                    f"   • Symbol: {symbol}\n"
                    f"   • Quantity: {filled_qty} shares\n"
                    f"   • Price: ${filled_price:.2f}\n"
                    f"   • Total Value: ${total_value:.2f}"
                )

            # If not filled immediately, try with a more aggressive price
            if filled_order.status != "filled":
                api.cancel_order(order.id)
                # More aggressive limit price (0.2% above ask for buy or below bid for sell)
                limit_price = round(
                    current_price * (1.002 if side == "buy" else 0.998), 2
                )

                order = api.submit_order(
                    symbol=symbol,
                    qty=quantity,
                    side=side,
                    type="limit",
                    time_in_force="day",
                    limit_price=limit_price,
                    extended_hours=True,
                )

                time.sleep(1)
                filled_order = api.get_order(order.id)

                if filled_order.status == "filled":
                    filled_price = float(filled_order.filled_avg_price)
                    filled_qty = float(filled_order.filled_qty)
                    total_value = filled_price * filled_qty
                    return (
                        f"✅ {side.upper()} order filled:\n"
                        f"   • Symbol: {symbol}\n"
                        f"   • Quantity: {filled_qty} shares\n"
                        f"   • Price: ${filled_price:.2f}\n"
                        f"   • Total Value: ${total_value:.2f}"
                    )
                else:
                    api.cancel_order(order.id)
                    return f"❌ Order not filled. Current {side} price: ${current_price:.2f}"

        except Exception as e:
            return f"❌ Order failed: {str(e)}"

    except Exception as e:
        error_msg = str(e).lower()
        if "insufficient buying power" in error_msg:
            return "❌ Insufficient buying power for this trade."
        elif "position" in error_msg:
            return "❌ Error with position size or current holdings."
        else:
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
