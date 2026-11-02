from decimal import Decimal
from models import Order
from orderbook import OrderBook


def dollars(cents: int) -> Decimal:
    return Decimal(cents) / 100


def main() -> None:
    book = OrderBook()
    book.submit(Order("S1", "sell", 10000, 5))
    book.submit(Order("S2", "sell", 10100, 5))
    quantity = 8
    best_price = book.sell_orders[0].price_cents
    fills = book.submit(Order("B1", "buy", 10100, quantity))
    total_cents = sum(t.price_cents * t.quantity for t in fills)
    filled = sum(t.quantity for t in fills)
    print("ORDER EXECUTION DEMO")
    for trade in fills:
        print(f"{trade.quantity} units at ${dollars(trade.price_cents):.2f}"
              f" = ${dollars(trade.price_cents * trade.quantity):.2f}")
    print(f"Total filled: {filled} of {quantity}")
    print(f"Total cost: ${dollars(total_cents):.2f}")
    if filled:
        print(f"Average price: ${dollars(total_cents) / filled:.3f}")
    naive_cost = best_price * filled
    print(f"Naive best-price estimate: ${dollars(naive_cost):.2f}")
    print(f"Extra execution cost: ${dollars(total_cents - naive_cost):.2f}")
    for order in book.sell_orders:
        print(f"Remaining {order.order_id}: {order.quantity} units"
              f" at ${dollars(order.price_cents):.2f}")


if __name__ == "__main__":
    main()
