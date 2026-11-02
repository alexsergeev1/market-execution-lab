import pytest
from models import Order
from orderbook import OrderBook, Trade


def test_partial_fill():
    book = OrderBook()
    original = Order("S2", "sell", 10100, 5)
    book.submit(original)
    book.submit(Order("S1", "sell", 10000, 5))
    fills = book.submit(Order("B1", "buy", 10100, 8))
    assert fills == [Trade("B1", "S1", 10000, 5), Trade("B1", "S2", 10100, 3)]
    assert sum(t.price_cents * t.quantity for t in fills) == 80300
    assert book.sell_orders == (Order("S2", "sell", 10100, 2),)
    assert book.buy_orders == ()
    assert book.trades == tuple(fills)
    assert original.quantity == 5


def test_highest_bid_first():
    book = OrderBook()
    book.submit(Order("B1", "buy", 10000, 5))
    book.submit(Order("B2", "buy", 10100, 5))
    fills = book.submit(Order("S1", "sell", 10000, 8))
    assert fills == [Trade("B2", "S1", 10100, 5), Trade("B1", "S1", 10000, 3)]
    assert book.buy_orders == (Order("B1", "buy", 10000, 2),)
    assert book.sell_orders == ()


@pytest.mark.parametrize("incoming_side", ["buy", "sell"])
def test_best_price_first(incoming_side):
    book = OrderBook()
    is_buy = incoming_side == "buy"
    resting_side = "sell" if is_buy else "buy"
    worse, better = (10100, 10000) if is_buy else (10000, 10100)
    book.submit(Order("early", resting_side, worse, 1))
    book.submit(Order("later", resting_side, better, 1))
    fills = book.submit(Order("incoming", incoming_side, worse, 1))
    assert len(fills) == 1
    assert fills[0].price_cents == better
    resting_id = fills[0].sell_order_id if is_buy else fills[0].buy_order_id
    assert resting_id == "later"


@pytest.mark.parametrize("incoming_side", ["buy", "sell"])
def test_same_price_order(incoming_side):
    book = OrderBook()
    is_buy = incoming_side == "buy"
    resting_side = "sell" if is_buy else "buy"
    book.submit(Order("first", resting_side, 10000, 3))
    book.submit(Order("second", resting_side, 10000, 3))
    book.submit(Order("take1", incoming_side, 10000, 1))
    fills = book.submit(Order("take2", incoming_side, 10000, 3))
    resting_ids = [t.sell_order_id if is_buy else t.buy_order_id for t in fills]
    assert resting_ids == ["first", "second"]
    assert [t.quantity for t in fills] == [2, 1]
    remaining = book.sell_orders if is_buy else book.buy_orders
    assert remaining == (Order("second", resting_side, 10000, 2),)


@pytest.mark.parametrize("incoming_side", ["buy", "sell"])
def test_price_limit(incoming_side):
    book = OrderBook()
    is_buy = incoming_side == "buy"
    resting_side = "sell" if is_buy else "buy"
    resting_price, limit = (10100, 10000) if is_buy else (10000, 10100)
    book.submit(Order("resting", resting_side, resting_price, 2))
    assert book.submit(Order("incoming", incoming_side, limit, 2)) == []
    assert len(book.buy_orders) == len(book.sell_orders) == 1
    assert book.trades == ()


@pytest.mark.parametrize("incoming_side", ["buy", "sell"])
def test_leftover_order(incoming_side):
    book = OrderBook()
    is_buy = incoming_side == "buy"
    resting_side = "sell" if is_buy else "buy"
    limit = 10100 if is_buy else 9900
    book.submit(Order("resting", resting_side, 10000, 2))
    incoming = Order("incoming", incoming_side, limit, 8)
    fills = book.submit(incoming)
    assert len(fills) == 1
    assert fills[0].price_cents == 10000
    assert fills[0].quantity == 2
    remaining = book.buy_orders if is_buy else book.sell_orders
    assert remaining == (Order("incoming", incoming_side, limit, 6),)
    assert incoming.quantity == 8


def test_cancel():
    book = OrderBook()
    book.submit(Order("B1", "buy", 9900, 1))
    book.submit(Order("S1", "sell", 10100, 1))
    assert book.cancel("B1") is True
    assert book.cancel("B1") is False
    assert book.cancel("missing") is False
    assert len(book.sell_orders) == 1
    assert book.cancel("S1") is True
    assert book.buy_orders == book.sell_orders == ()


@pytest.mark.parametrize("state", ["active", "filled", "cancelled"])
def test_duplicate_id(state):
    book = OrderBook()
    book.submit(Order("original", "buy", 10000, 1))
    if state == "filled":
        book.submit(Order("seller", "sell", 10000, 1))
        assert book.cancel("original") is False
    elif state == "cancelled":
        book.cancel("original")
    before = (book.buy_orders, book.sell_orders, book.trades)
    with pytest.raises(ValueError, match="order_id"):
        book.submit(Order("original", "sell", 9900, 1))
    assert (book.buy_orders, book.sell_orders, book.trades) == before


def test_bad_input():
    book = OrderBook()
    with pytest.raises(TypeError, match="Order"):
        book.submit("not an order")
    assert book.buy_orders == book.sell_orders == book.trades == ()


def test_snapshot():
    book = OrderBook()
    book.submit(Order("B1", "buy", 10000, 1))
    before = book.buy_orders
    book.submit(Order("B2", "buy", 10000, 1))
    assert isinstance(before, tuple)
    assert len(before) == 1
    assert len(book.buy_orders) == 2


def test_separate_books():
    first, second = OrderBook(), OrderBook()
    order = Order("same-id", "buy", 10000, 1)
    first.submit(order)
    assert second.buy_orders == ()
    second.submit(order)
    first.cancel("same-id")
    assert len(second.buy_orders) == 1


def test_trade_history():
    book = OrderBook()
    book.submit(Order("S1", "sell", 10000, 2))
    fills = book.submit(Order("B1", "buy", 10000, 1))
    fills.clear()
    book.submit(Order("B2", "buy", 10000, 1))
    assert book.trades == (
        Trade("B1", "S1", 10000, 1),
        Trade("B2", "S1", 10000, 1),
    )
