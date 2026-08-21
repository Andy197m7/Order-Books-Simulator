"""
Market maker bot — continuously quotes bids and asks around mid-price,
providing liquidity to the book.
"""
from __future__ import annotations
import asyncio
import json
import random
import uuid
import time
import redis.asyncio as aioredis
from engine.order import Side, OrderType, OrderStatus


SPREAD_HALF = 0.50   # half-spread in dollars
QUOTE_SIZE  = 50     # shares per side
REFRESH_MS  = 800    # quote refresh interval


async def run(redis_client: aioredis.Redis, engine_ref) -> None:
    bid_id: str | None = None
    ask_id: str | None = None

    async def cancel(oid: str | None) -> None:
        if oid:
            payload = json.dumps({"action": "cancel", "order_id": oid})
            await redis_client.rpush("order_queue", payload)

    async def post_limit(side: Side, price: float, qty: int) -> str:
        oid = str(uuid.uuid4())
        order = {
            "id": oid,
            "side": side.value,
            "order_type": OrderType.LIMIT.value,
            "price": round(price, 2),
            "quantity": qty,
            "remaining": qty,
            "timestamp": time.time(),
            "status": OrderStatus.OPEN.value,
            "client_id": "market_maker",
        }
        await redis_client.rpush("order_queue", json.dumps(order))
        return oid

    while True:
        try:
            mid = engine_ref.last_trade_price
            noise = random.uniform(-0.05, 0.05)

            await cancel(bid_id)
            await cancel(ask_id)
            await asyncio.sleep(0.05)  # brief pause so cancels land first

            bid_id = await post_limit(Side.BUY,  mid - SPREAD_HALF + noise, QUOTE_SIZE)
            ask_id = await post_limit(Side.SELL, mid + SPREAD_HALF + noise, QUOTE_SIZE)

            await asyncio.sleep(REFRESH_MS / 1000)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[market_maker] {exc}")
            await asyncio.sleep(0.5)
