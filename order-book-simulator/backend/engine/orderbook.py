from __future__ import annotations
from collections import deque
from sortedcontainers import SortedDict
from typing import Optional, List, Tuple, Dict
from .order import Order, Side, OrderStatus


class OrderBook:
    def __init__(self) -> None:
        # Bids: highest price first — negate key so SortedDict gives descending order
        self._bids: SortedDict = SortedDict(lambda k: -k)
        # Asks: lowest price first — natural ascending order
        self._asks: SortedDict = SortedDict()
        # O(1) order lookup for cancellations
        self._orders: Dict[str, Order] = {}

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add_order(self, order: Order) -> None:
        self._orders[order.id] = order
        book = self._bids if order.side == Side.BUY else self._asks
        if order.price not in book:
            book[order.price] = deque()
        book[order.price].append(order)

    def cancel_order(self, order_id: str) -> Optional[Order]:
        order = self._orders.get(order_id)
        if not order or order.status not in (OrderStatus.OPEN, OrderStatus.PARTIAL):
            return None
        order.status = OrderStatus.CANCELLED
        book = self._bids if order.side == Side.BUY else self._asks
        if order.price in book:
            try:
                book[order.price].remove(order)
            except ValueError:
                pass
            if not book[order.price]:
                del book[order.price]
        self._orders.pop(order_id, None)
        return order

    def consume_resting(self, resting: Order, qty: int) -> None:
        """Reduce resting order quantity after a partial or full fill."""
        resting.remaining -= qty
        book = self._bids if resting.side == Side.BUY else self._asks
        price = resting.price
        if resting.remaining <= 0:
            resting.status = OrderStatus.FILLED
            if price in book:
                try:
                    book[price].remove(resting)
                except ValueError:
                    pass
            self._orders.pop(resting.id, None)
        else:
            resting.status = OrderStatus.PARTIAL
        if price in book and not book[price]:
            del book[price]

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def best_bid(self) -> Optional[float]:
        return next(iter(self._bids)) if self._bids else None

    def best_ask(self) -> Optional[float]:
        return next(iter(self._asks)) if self._asks else None

    def mid_price(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        if bb is not None and ba is not None:
            return round((bb + ba) / 2, 2)
        return bb or ba

    def spread(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        if bb is not None and ba is not None:
            return round(ba - bb, 2)
        return None

    def peek_best_bid(self) -> Optional[Order]:
        for price in self._bids:
            if self._bids[price]:
                return self._bids[price][0]
        return None

    def peek_best_ask(self) -> Optional[Order]:
        for price in self._asks:
            if self._asks[price]:
                return self._asks[price][0]
        return None

    def available_liquidity(self, side: Side) -> int:
        """Total quantity on the opposite side (what an aggressor can fill against)."""
        book = self._asks if side == Side.BUY else self._bids
        return sum(o.remaining for q in book.values() for o in q)

    def get_bids(self, levels: int = 10) -> List[Tuple[float, int]]:
        result = []
        for price in list(self._bids.keys())[:levels]:
            qty = sum(o.remaining for o in self._bids[price])
            result.append((price, qty))
        return result

    def get_asks(self, levels: int = 10) -> List[Tuple[float, int]]:
        result = []
        for price in list(self._asks.keys())[:levels]:
            qty = sum(o.remaining for o in self._asks[price])
            result.append((price, qty))
        return result

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def snapshot(self, levels: int = 10) -> dict:
        bids = self.get_bids(levels)
        asks = self.get_asks(levels)
        return {
            "bids": [{"price": p, "quantity": q} for p, q in bids],
            "asks": [{"price": p, "quantity": q} for p, q in asks],
            "spread": self.spread(),
            "mid_price": self.mid_price(),
        }
