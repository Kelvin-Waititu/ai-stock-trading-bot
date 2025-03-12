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
        current_position_qty = 0
        current_position_value = 0
        try:
            position = api.get_position(symbol)
            if position:
                current_position_qty = abs(int(position.qty))  # Use absolute value
                current_position_value = abs(
                    float(position.market_value)
                )  # Use absolute value
        except Exception as e:
            if "no position available" not in str(e).lower():
                print(f"Error checking position: {str(e)}")

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
            try:
                # Double-check position exists and quantity
                position = api.get_position(symbol)
                current_position_qty = abs(int(position.qty))

                if current_position_qty <= 0:
                    return (
                        "❌ No Position Found:\n"
                        f"Symbol: {symbol}\n"
                        "You must own shares before selling."
                    )

                # Use provided quantity or sell entire position
                quantity = quantity if quantity else current_position_qty
                if quantity > current_position_qty:
                    return (
                        "❌ Invalid Sell Quantity:\n"
                        f"Attempting to sell: {quantity} shares\n"
                        f"Current position: {current_position_qty} shares\n"
                        "You cannot sell more shares than you own."
                    )

            except Exception as e:
                if "no position available" in str(e).lower():
                    return (
                        "❌ No Position Found:\n"
                        f"Symbol: {symbol}\n"
                        "You must own shares before selling."
                    )
                return f"❌ Error verifying position: {str(e)}"

        # Try to place the order
        try:
            # First attempt - market order during regular hours
            if not api.get_clock().is_open:
                # More aggressive limit price for extended hours
                limit_price = round(
                    current_price * (1.005 if side == "buy" else 0.995), 2
                )
                order_type = "limit"
                time_in_force = "day"
                extended_hours = True
            else:
                # During market hours, use market orders
                order_type = "market"
                time_in_force = "day"
                extended_hours = False
                limit_price = None

            # Submit order
            order = api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                extended_hours=extended_hours,
            )

            # Wait for fill - longer during extended hours
            wait_time = 5 if api.get_clock().is_open else 10
            time.sleep(wait_time)

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

            # If not filled, try again with more aggressive pricing
            if filled_order.status != "filled":
                api.cancel_order(order.id)

                # Even more aggressive limit price
                limit_price = round(
                    current_price * (1.01 if side == "buy" else 0.99), 2
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

                time.sleep(wait_time)
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
                    return (
                        f"❌ Order not filled. Try during market hours (9:30 AM - 4:00 PM ET)\n"
                        f"Current {side} price: ${current_price:.2f}"
                    )

        except Exception as e:
            error_str = str(e).lower()
            if "wash" in error_str:
                return (
                    "❌ Wash Trade Prevention:\n"
                    "A wash trade occurs when you try to buy and sell the same stock too quickly.\n"
                    "To avoid this:\n"
                    "1. Wait a few minutes between trades\n"
                    "2. Try trading a different quantity\n"
                    "3. Consider trading during market hours\n"
                    f"Current {side} price: ${current_price:.2f}"
                )
            return f"❌ Order failed: {str(e)}"

    except Exception as e:
        error_msg = str(e).lower()
        if "insufficient buying power" in error_msg:
            return (
                "❌ Insufficient Buying Power:\n"
                f"Required: ${quantity * current_price:.2f}\n"
                f"Available: ${buying_power:.2f}"
            )
        elif "position" in error_msg:
            return (
                "❌ Position Error:\n"
                f"Current Position: {current_position_qty} shares\n"
                f"Attempting to trade: {quantity} shares\n"
                f"Current Price: ${current_price:.2f}"
            )
        elif "wash" in error_msg:
            return (
                "❌ Wash Trade Prevention:\n"
                "A wash trade occurs when you try to buy and sell the same stock too quickly.\n"
                "To avoid this:\n"
                "1. Wait a few minutes between trades\n"
                "2. Try trading a different quantity\n"
                "3. Consider trading during market hours\n"
                f"Current {side} price: ${current_price:.2f}"
            )
        else:
            return (
                f"❌ Trade Error:\n"
                f"Symbol: {symbol}\n"
                f"Action: {side.upper()}\n"
                f"Quantity: {quantity}\n"
                f"Price: ${current_price:.2f}\n"
                f"Error: {str(e)}"
            )


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
