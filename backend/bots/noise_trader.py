"""
Noise trader — submits random limit and market orders to simulate
realistic volume and price discovery.
"""
from __future__ import annotations
import asyncio
import json
import random
import uuid
import time
import redis.asyncio as aioredis
from engine.order import Side, OrderType, OrderStatus


async def run(redis_client: aioredis.Redis, engine_ref) -> None:
    while True:
        try:
            delay = random.uniform(0.4, 1.5)
            await asyncio.sleep(delay)

            side = random.choice([Side.BUY, Side.SELL])
            qty  = random.randint(5, 100)
            mid  = engine_ref.last_trade_price
            use_market = random.random() < 0.25

            oid = str(uuid.uuid4())
            if use_market:
                order = {
                    "id": oid,
                    "side": side.value,
                    "order_type": OrderType.MARKET.value,
                    "price": None,
                    "quantity": qty,
                    "remaining": qty,
                    "timestamp": time.time(),
                    "status": OrderStatus.OPEN.value,
                    "client_id": "noise",
                }
            else:
                offset = random.uniform(-1.5, 1.5)
                price  = round(mid + offset, 2)
                order = {
                    "id": oid,
                    "side": side.value,
                    "order_type": OrderType.LIMIT.value,
                    "price": price,
                    "quantity": qty,
                    "remaining": qty,
                    "timestamp": time.time(),
                    "status": OrderStatus.OPEN.value,
                    "client_id": "noise",
                }

            await redis_client.rpush("order_queue", json.dumps(order))

        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[noise_trader] {exc}")
            await asyncio.sleep(0.5)
