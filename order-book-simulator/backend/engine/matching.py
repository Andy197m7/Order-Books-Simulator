from __future__ import annotations
import asyncio
import json
from typing import Optional
import redis.asyncio as aioredis

from .order import Order, Side, OrderType, OrderStatus, Trade
from .orderbook import OrderBook


class MatchingEngine:
    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.book = OrderBook()
        self.redis = redis_client
        self.last_trade_price: float = 100.0
        self.running = False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        self.running = True
        while self.running:
            try:
                result = await self.redis.blpop("order_queue", timeout=0.05)
                if result:
                    _, raw = result
                    data = json.loads(raw)
                    if data.get("action") == "cancel":
                        await self._handle_cancel(data["order_id"])
                    else:
                        order = Order.from_dict(data)
                        await self.process_order(order)
                    await self._publish_book_update()
            except asyncio.CancelledError:
                self.running = False
                break
            except Exception as exc:
                print(f"[engine] error: {exc}")
                await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Order dispatch
    # ------------------------------------------------------------------

    async def process_order(self, order: Order) -> None:
        if order.order_type == OrderType.MARKET:
            await self._match_market(order)
        elif order.order_type == OrderType.LIMIT:
            await self._match_limit(order)
        elif order.order_type == OrderType.IOC:
            await self._match_ioc(order)
        elif order.order_type == OrderType.FOK:
            await self._match_fok(order)

    async def _handle_cancel(self, order_id: str) -> None:
        cancelled = self.book.cancel_order(order_id)
        if cancelled:
            await self._publish_order_status(cancelled)

    # ------------------------------------------------------------------
    # Matching logic
    # ------------------------------------------------------------------

    async def _match_market(self, order: Order) -> None:
        while order.remaining > 0:
            resting = (
                self.book.peek_best_ask()
                if order.side == Side.BUY
                else self.book.peek_best_bid()
            )
            if resting is None:
                break
            fill_qty = min(order.remaining, resting.remaining)
            await self._execute_fill(order, resting, resting.price, fill_qty)

        if order.remaining > 0:
            order.status = OrderStatus.CANCELLED
        await self._publish_order_status(order)

    async def _match_limit(self, order: Order) -> None:
        while order.remaining > 0:
            if order.side == Side.BUY:
                resting = self.book.peek_best_ask()
                if resting is None or resting.price > order.price:
                    break
            else:
                resting = self.book.peek_best_bid()
                if resting is None or resting.price < order.price:
                    break

            fill_qty = min(order.remaining, resting.remaining)
            fill_price = resting.price
            await self._execute_fill(order, resting, fill_price, fill_qty)

        if order.remaining > 0:
            order.status = OrderStatus.PARTIAL if order.status == OrderStatus.PARTIAL else OrderStatus.OPEN
            self.book.add_order(order)

        await self._publish_order_status(order)

    async def _match_ioc(self, order: Order) -> None:
        while order.remaining > 0:
            if order.side == Side.BUY:
                resting = self.book.peek_best_ask()
                if resting is None or resting.price > order.price:
                    break
            else:
                resting = self.book.peek_best_bid()
                if resting is None or resting.price < order.price:
                    break
            fill_qty = min(order.remaining, resting.remaining)
            await self._execute_fill(order, resting, resting.price, fill_qty)

        if order.remaining > 0:
            order.status = OrderStatus.CANCELLED
        await self._publish_order_status(order)

    async def _match_fok(self, order: Order) -> None:
        available = self.book.available_liquidity(order.side)
        if available < order.remaining:
            order.status = OrderStatus.REJECTED
            await self._publish_order_status(order)
            return
        # Inline market fill — must not set CANCELLED if book empties (treat as REJECTED)
        while order.remaining > 0:
            resting = (
                self.book.peek_best_ask()
                if order.side == Side.BUY
                else self.book.peek_best_bid()
            )
            if resting is None:
                break
            fill_qty = min(order.remaining, resting.remaining)
            await self._execute_fill(order, resting, resting.price, fill_qty)
        if order.remaining > 0:
            order.status = OrderStatus.REJECTED
        await self._publish_order_status(order)

    # ------------------------------------------------------------------
    # Fill execution
    # ------------------------------------------------------------------

    async def _execute_fill(
        self, aggressor: Order, resting: Order, price: float, qty: int
    ) -> Trade:
        aggressor.remaining -= qty
        aggressor.status = OrderStatus.FILLED if aggressor.remaining == 0 else OrderStatus.PARTIAL

        self.book.consume_resting(resting, qty)
        self.last_trade_price = price

        buyer_id = aggressor.client_id if aggressor.side == Side.BUY else resting.client_id
        seller_id = resting.client_id if aggressor.side == Side.BUY else aggressor.client_id

        trade = Trade.create(buyer_id, seller_id, price, qty, aggressor.side)
        await self._publish_trade(trade)
        await self._publish_order_status(resting)
        return trade

    # ------------------------------------------------------------------
    # Redis publishing
    # ------------------------------------------------------------------

    async def _publish_trade(self, trade: Trade) -> None:
        await self.redis.publish("events", json.dumps(trade.to_dict()))

    async def _publish_order_status(self, order: Order) -> None:
        payload = {
            "type": "order_status",
            "id": order.id,
            "status": order.status.value,
            "remaining": order.remaining,
            "client_id": order.client_id,
        }
        await self.redis.publish("events", json.dumps(payload))

    async def _publish_book_update(self) -> None:
        snap = self.book.snapshot(10)
        snap["type"] = "order_book_update"
        await self.redis.publish("events", json.dumps(snap))
