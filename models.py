from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Order:
    order_id: str
    side: Literal["buy", "sell"]
    price_cents: int
    quantity: int

    def __post_init__(self) -> None:
        if not isinstance(self.order_id, str) or not self.order_id.strip():
            raise ValueError("order_id must be a nonempty string")
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        if type(self.price_cents) is not int or self.price_cents <= 0:
            raise ValueError("price_cents must be a positive integer")
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        