from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import uuid
import time


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"
    IOC = "ioc"
    FOK = "fok"


class OrderStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    id: str
    side: Side
    order_type: OrderType
    price: Optional[float]
    quantity: int
    remaining: int
    timestamp: float
    status: OrderStatus
    client_id: str = "user"

    @classmethod
    def create(
        cls,
        side: Side,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None,
        client_id: str = "user",
    ) -> "Order":
        return cls(
            id=str(uuid.uuid4()),
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity,
            remaining=quantity,
            timestamp=time.time(),
            status=OrderStatus.OPEN,
            client_id=client_id,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "price": self.price,
            "quantity": self.quantity,
            "remaining": self.remaining,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "client_id": self.client_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls(
            id=data["id"],
            side=Side(data["side"]),
            order_type=OrderType(data["order_type"]),
            price=data.get("price"),
            quantity=data["quantity"],
            remaining=data["remaining"],
            timestamp=data["timestamp"],
            status=OrderStatus(data["status"]),
            client_id=data.get("client_id", "user"),
        )


@dataclass
class Trade:
    id: str
    buyer_id: str
    seller_id: str
    price: float
    quantity: int
    timestamp: float
    aggressor_side: Side

    @classmethod
    def create(
        cls,
        buyer_id: str,
        seller_id: str,
        price: float,
        quantity: int,
        aggressor_side: Side,
    ) -> "Trade":
        return cls(
            id=str(uuid.uuid4()),
            buyer_id=buyer_id,
            seller_id=seller_id,
            price=price,
            quantity=quantity,
            timestamp=time.time(),
            aggressor_side=aggressor_side,
        )

    def to_dict(self) -> dict:
        return {
            "type": "trade_executed",
            "id": self.id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "price": self.price,
            "quantity": self.quantity,
            "timestamp": self.timestamp,
            "aggressor_side": self.aggressor_side.value,
        }
