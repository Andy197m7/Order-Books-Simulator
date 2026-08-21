# Order Book Simulator

A real-time limit order book simulator with a matching engine, simulated market participants, and a live trading dashboard.

## Architecture

```
Browser (React + TypeScript)
    ↕ WebSocket / REST
FastAPI (Python)
    ↕ Redis pub/sub + list queue
Matching Engine
    ↑ orders submitted by bots + user
```

### Backend

| File | Purpose |
|------|---------|
| `engine/order.py` | `Order`, `Trade` dataclasses; `Side`, `OrderType`, `OrderStatus` enums |
| `engine/orderbook.py` | SortedDict-backed bid/ask book; FIFO queues per price level; O(1) cancel |
| `engine/matching.py` | Matching engine loop; LIMIT, MARKET, IOC, FOK order types; Redis pub/sub |
| `bots/market_maker.py` | Continuously quotes ±$0.50 around mid-price, refreshes every 800 ms |
| `bots/momentum.py` | Buys/sells on 3 consecutive up or down ticks |
| `bots/noise_trader.py` | Random limit and market orders for realistic volume |
| `main.py` | FastAPI app; REST + WebSocket endpoints; bot coroutines |

### Frontend

| Component | Purpose |
|-----------|---------|
| `OrderBook` | Live bid/ask ladder with depth bars that flash on change |
| `PriceChart` | Tick-by-tick line chart via TradingView Lightweight Charts |
| `TradeTape` | Scrolling time & sales feed (last 200 trades) |
| `OrderEntry` | Order form — BUY/SELL, LIMIT/MARKET/IOC/FOK |

## Quick Start

**Requirements:** Docker and Docker Compose.

```bash
git clone <repo-url>
cd order-book-simulator
docker-compose up --build
```

Open [http://localhost:3000](http://localhost:3000).

## API

```
POST   /order          Submit a limit, market, IOC, or FOK order
DELETE /order/{id}     Cancel a resting order
GET    /orderbook      Top 10 bid/ask levels snapshot
WS     /stream         Real-time event stream (trade_executed, order_book_update, order_status)
```

### Submit order

```json
POST /order
{
  "side": "buy",
  "order_type": "limit",
  "price": 99.50,
  "quantity": 100
}
```

### WebSocket events

**trade_executed**
```json
{ "type": "trade_executed", "price": 99.50, "quantity": 60, "aggressor_side": "buy", ... }
```

**order_book_update**
```json
{ "type": "order_book_update", "bids": [...], "asks": [...], "spread": 1.00, "mid_price": 100.00 }
```

**order_status**
```json
{ "type": "order_status", "id": "...", "status": "filled", "remaining": 0 }
```

## Order Types

| Type | Behavior |
|------|---------|
| `limit` | Rests in book if it doesn't cross the spread; executes at limit price or better |
| `market` | Walks the opposite side until filled or book is empty |
| `ioc` | Fills what it can immediately, cancels the rest |
| `fok` | Fills completely or rejects entirely |

## Development

Run services individually without Docker:

```bash
# Start Redis
redis-server

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Stack

- **Python 3.12** — matching engine and bots
- **FastAPI** — REST + WebSocket API
- **Redis** — order queue (list) and event bus (pub/sub)
- **sortedcontainers** — SortedDict for the order book
- **React 18 + TypeScript** — dashboard
- **TradingView Lightweight Charts** — price chart
- **Vite** — frontend build tool
- **Docker Compose** — orchestration
