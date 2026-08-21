from __future__ import annotations
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from engine.order import Order, Side, OrderType, OrderStatus
from engine.matching import MatchingEngine
import bots.market_maker as mm_bot
import bots.momentum as mo_bot
import bots.noise_trader as noise_bot


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class OrderRequest(BaseModel):
    side: str
    order_type: str
    price: Optional[float] = None
    quantity: int

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        if v not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        return v

    @field_validator("order_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("limit", "market", "ioc", "fok"):
            raise ValueError("order_type must be limit|market|ioc|fok")
        return v


# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

redis_client: aioredis.Redis
engine: MatchingEngine
_bg_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, engine

    redis_client = aioredis.from_url("redis://redis:6379", decode_responses=True)
    engine = MatchingEngine(redis_client)

    # Flush stale queue from previous run
    await redis_client.delete("order_queue")
    _bg_tasks.clear()

    loop = asyncio.get_running_loop()
    _bg_tasks.append(loop.create_task(engine.run()))
    _bg_tasks.append(loop.create_task(mm_bot.run(redis_client, engine)))
    _bg_tasks.append(loop.create_task(mo_bot.run(redis_client, engine)))
    _bg_tasks.append(loop.create_task(noise_bot.run(redis_client, engine)))

    yield

    for t in _bg_tasks:
        t.cancel()
    await asyncio.gather(*_bg_tasks, return_exceptions=True)
    await redis_client.aclose()


app = FastAPI(title="Order Book Simulator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.post("/order")
async def submit_order(req: OrderRequest):
    if req.order_type == "limit" and req.price is None:
        raise HTTPException(400, "limit orders require a price")

    order = Order.create(
        side=Side(req.side),
        order_type=OrderType(req.order_type),
        quantity=req.quantity,
        price=req.price,
        client_id="user",
    )
    await redis_client.rpush("order_queue", json.dumps(order.to_dict()))
    return {"order_id": order.id, "status": "submitted"}


@app.delete("/order/{order_id}")
async def cancel_order(order_id: str):
    await redis_client.rpush("order_queue", json.dumps({"action": "cancel", "order_id": order_id}))
    return {"order_id": order_id, "status": "cancel_requested"}


@app.get("/orderbook")
async def get_orderbook():
    return engine.book.snapshot(10)


# ---------------------------------------------------------------------------
# WebSocket stream
# ---------------------------------------------------------------------------

@app.websocket("/stream")
async def websocket_stream(ws: WebSocket):
    await ws.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("events")

    # Send current book snapshot immediately on connect
    await ws.send_text(json.dumps({**engine.book.snapshot(10), "type": "order_book_update"}))

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await ws.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[ws] {exc}")
    finally:
        await pubsub.unsubscribe("events")
        await pubsub.aclose()
