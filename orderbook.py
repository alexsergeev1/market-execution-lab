# Limit orders only. No fees or live trading.
from dataclasses import dataclass, replace
from models import Order


@dataclass(frozen=True)
class Trade:
    buy_order_id: str
    sell_order_id: str
    price_cents: int
    quantity: int


class OrderBook:
    def __init__(self) -> None:
        self._buy_orders: list[Order] = []
        self._sell_orders: list[Order] = []
        self._trades: list[Trade] = []
        self._seen_ids: set[str] = set()

    @property
    def buy_orders(self) -> tuple[Order, ...]:
        return tuple(self._buy_orders)

    @property
    def sell_orders(self) -> tuple[Order, ...]:
        return tuple(self._sell_orders)

    @property
    def trades(self) -> tuple[Trade, ...]:
        return tuple(self._trades)

    def submit(self, order: Order) -> list[Trade]:
        if not isinstance(order, Order):
            raise TypeError("submit requires an Order")
        if order.order_id in self._seen_ids:
            raise ValueError("order_id has already been used")
        self._seen_ids.add(order.order_id)

        is_buy = order.side == "buy"
        opposite = self._sell_orders if is_buy else self._buy_orders
        remaining = order.quantity
        fills: list[Trade] = []

        while remaining > 0 and opposite:
            resting = opposite[0]
            if is_buy and order.price_cents < resting.price_cents:
                break
            if not is_buy and order.price_cents > resting.price_cents:
                break

            quantity = min(remaining, resting.quantity)
            fills.append(Trade(
                buy_order_id=order.order_id if is_buy else resting.order_id,
                sell_order_id=resting.order_id if is_buy else order.order_id,
                price_cents=resting.price_cents,
                quantity=quantity,
            ))
            remaining -= quantity
            if quantity == resting.quantity:
                opposite.pop(0)
            else:
                # Keep its spot.
                opposite[0] = replace(
                    resting, quantity=resting.quantity - quantity
                )

        if remaining > 0:
            own_side = self._buy_orders if is_buy else self._sell_orders
            own_side.append(replace(order, quantity=remaining))
            # Same price: oldest order first.
            own_side.sort(key=lambda item: item.price_cents, reverse=is_buy)

        self._trades.extend(fills)
        return fills

    def cancel(self, order_id: str) -> bool:
        for orders in (self._buy_orders, self._sell_orders):
            for index, order in enumerate(orders):
                if order.order_id == order_id:
                    orders.pop(index)
                    return True
        return False
