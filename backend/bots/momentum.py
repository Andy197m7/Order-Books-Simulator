"""
Momentum trader — buys when price ticks up 3 times in a row,
sells when it ticks down 3 times in a row.
"""
from __future__ import annotations
import asyncio
import json
import uuid
import time
import redis.asyncio as aioredis
from engine.order import Side, OrderType, OrderStatus


TRADE_SIZE = 30
COOLDOWN   = 2.0  # seconds between trades


async def run(redis_client: aioredis.Redis, engine_ref) -> None:
    prices: list[float] = []
    last_trade = 0.0

    async def submit_market(side: Side, qty: int) -> None:
        oid = str(uuid.uuid4())
        order = {
            "id": oid,
            "side": side.value,
            "order_type": OrderType.MARKET.value,
            "price": None,
            "quantity": qty,
            "remaining": qty,
            "timestamp": time.time(),
            "status": OrderStatus.OPEN.value,
            "client_id": "momentum",
        }
        await redis_client.rpush("order_queue", json.dumps(order))

    while True:
        try:
            await asyncio.sleep(0.3)
            current = engine_ref.last_trade_price
            prices.append(current)
            if len(prices) > 5:
                prices.pop(0)

            if len(prices) < 4:
                continue

            now = time.time()
            if now - last_trade < COOLDOWN:
                continue

            ticks = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
            if all(t > 0 for t in ticks[-3:]):
                await submit_market(Side.BUY, TRADE_SIZE)
                last_trade = now
            elif all(t < 0 for t in ticks[-3:]):
                await submit_market(Side.SELL, TRADE_SIZE)
                last_trade = now

        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[momentum] {exc}")
            await asyncio.sleep(0.5)
