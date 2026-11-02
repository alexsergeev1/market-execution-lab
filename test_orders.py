import pytest
from models import Order

@pytest.mark.parametrize("side", ["buy", "sell"])
def test_valid_order(side):
    order = Order("A1", side, 10100, 8)
    assert order.order_id == "A1"
    assert order.side == side
    assert order.price_cents == 10100
    assert order.quantity == 8

@pytest.mark.parametrize("field,value", [
    ("order_id", ""),
    ("side", "hold"),
    ("price_cents", 0),
    ("price_cents", -100),
    ("price_cents", 100.5),
    ("price_cents", True),
    ("quantity", 0),
    ("quantity", -1),
    ("quantity", 1.5),
    ("quantity", True),
])
def test_invalid_order(field, value):
    data = dict(order_id="A1", side="buy", price_cents=10100, quantity=8)
    data[field] = value
    with pytest.raises(ValueError, match=field):
        Order(**data)