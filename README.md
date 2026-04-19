# Limit Order Book Simulator

A high-performance, async limit order book (LOB) simulator built in Python. Designed to mimic core exchange mechanics — price-time priority matching, real-time WebSocket streaming, OHLCV candlestick generation, and persistent trade history — all in a local development environment.

---

## Overview

This project simulates a central limit order book (CLOB) as found in real financial exchanges. It supports:

- **Price-time priority matching** — orders are matched against the best available opposing price, with FIFO queue ordering at each price level
- **Real-time market data streaming** — via a WebSocket server broadcasting live trades and order book snapshots
- **Historical trade queries** — with full OHLCV (Open, High, Low, Close, Volume) aggregation via SQL
- **Interactive order entry** — a terminal-based client for submitting live buy/sell orders
- **Prototype visualizations** — candlestick charts with SMA overlays using `mplfinance`

---

## Project Structure

```
limit-order-book-simulator/
├── simulator/                   # Core production simulator
│   ├── OrderBook.py             # Async limit order book engine
│   ├── MarketDataServer.py      # WebSocket server for market data
│   ├── OrderServer.py           # WebSocket server for order submission
│   ├── interactive_client.py    # Terminal-based interactive trading client
│   ├── hardcoded_client.py      # Scripted test client (sends fixed orders)
│   ├── main.py                  # Entry point
│   └── bloomberg/
│       └── index.html           # Bloomberg-style frontend (WIP)
│
├── prototype/                   # Early research & experimentation
│   ├── order_book.py            # Synchronous LOB with matplotlib charting
│   ├── real_time_plot.py        # Real-time price plotting via threading
│   ├── plt_only.py              # Standalone candlestick chart prototype
│   ├── socket_exchange_1.py     # First socket-based exchange prototype
│   ├── json_socket_ex.py        # JSON-over-socket prototype
│   ├── json_client.py           # Client for JSON socket exchange
│   └── client_1.py              # Basic socket client
│
├── plots/                       # Saved chart output
├── requirements.txt
└── README.md
```

---

## Architecture

### `OrderBook.py` — The Matching Engine

The heart of the simulator. Built on `asyncio` for non-blocking, concurrent order processing.

| Feature | Detail |
|---|---|
| **Data structure** | `SortedDict` (via `sortedcontainers`) for O(log n) bid/ask price level access |
| **Matching algorithm** | Price-time priority (FIFO at each level) |
| **Concurrency** | `asyncio.Lock` guards all book mutations |
| **Trade persistence** | SQLite with batched inserts (configurable batch size, default: 100) + periodic flush every 5s |
| **Event system** | `asyncio.Queue` for pushing trade events to downstream consumers |
| **OHLCV queries** | SQL window functions over the `trades` table with time-bucketing |

**Order lifecycle:**
```
Submit Order → Validate → Match Against Opposite Side → Record Trades → Add Remainder to Book
```

### `MarketDataServer.py` — Market Data WebSocket Server

Serves two types of real-time data to connected clients:

| Feed | Mechanism | Default Interval |
|---|---|---|
| **Order Book Snapshots** | Periodic broadcast | 500ms |
| **Trade Events** | Event-driven push | On match |

Clients subscribe/unsubscribe to feeds by sending JSON control messages:

```json
{ "type": "subscribe_trades" }
{ "type": "subscribe_order_book" }
{ "type": "request_historical_ohlc", "from_time": 1700000000, "to_time": 1700003600, "candle_interval": 60 }
```

### `interactive_client.py` — Terminal Trading Client

A WebSocket client with an interactive console for submitting limit orders:

```
Side (b/s) or 'q' to quit: b
Limit price: 102.50
Quantity: 5
Sent order: {"side": "buy", "price": 102.5, "quantity": 5}
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Recommended: virtual environment

### Installation

```bash
git clone https://github.com/rogelio-9/limit-order-book-simulator.git
cd limit-order-book-simulator

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---|---|
| `websockets` | Async WebSocket server |
| `websocket-client` | Synchronous WebSocket client |
| `sortedcontainers` | Efficient sorted bid/ask price levels |
| `aiosqlite` / `sqlite3` | Trade persistence |
| `numpy` | Order generation (prototype) |
| `pandas` | Trade aggregation & OHLCV resampling |
| `matplotlib` | Charting (prototype) |
| `mplfinance` | Candlestick charts (prototype) |

### Running the Simulator

**1. Start the exchange (order book + market data server):**
```bash
python simulator/main.py
```

**2. Connect an interactive trading client (in a new terminal):**
```bash
python simulator/interactive_client.py
```

**3. Or replay scripted orders with the hardcoded client:**
```bash
python simulator/hardcoded_client.py
```

### Running the Prototype

The prototype includes a fully self-contained order book simulation with candlestick charting. No server needed:

```bash
python prototype/order_book.py
```

This runs a 60-second simulation with 500 randomly generated orders and saves a candlestick chart to `ticker_plot.png`.

---

## WebSocket API Reference

All messages are JSON. Connect to `ws://127.0.0.1:8765` (Order Server) or `ws://127.0.0.1:8766` (Market Data Server).

### Client → Server

| Message Type | Description |
|---|---|
| `subscribe_trades` | Subscribe to real-time trade feed |
| `unsubscribe_trades` | Unsubscribe from trade feed |
| `subscribe_order_book` | Subscribe to periodic order book snapshots |
| `unsubscribe_order_book` | Unsubscribe from order book snapshots |
| `request_historical` | Fetch raw historical trades in a time range |
| `request_historical_ohlc` | Fetch OHLCV candles in a time range |

### Server → Client

| Message Type | Description |
|---|---|
| `new_trades` | Fired on each successful match |
| `order_book_update` | Periodic order book snapshot (bids, asks, last price) |
| `historical_trades` | Response to `request_historical` |
| `historical_ohlc` | Response to `request_historical_ohlc` |

**Example `order_book_update` payload:**
```json
{
  "type": "order_book_update",
  "data": {
    "bids": { "101.0": [...], "100.5": [...] },
    "asks": { "101.5": [...], "102.0": [...] },
    "last_price": 101.0,
    "recent_trades": [...]
  }
}
```

---

##  Database Schema

Trades are persisted in a local SQLite database (`trades.db`):

```sql
CREATE TABLE trades (
    timestamp REAL,     -- Unix timestamp (float)
    buyer_id  TEXT,
    seller_id TEXT,
    price     REAL,
    quantity  INTEGER
);

CREATE INDEX idx_timestamp ON trades(timestamp);
```

OHLCV queries use SQL window functions to bucket trades into time intervals on the fly — no pre-aggregation needed.

---

## Roadmap

- [ ] Order Server (`OrderServer.py`) — full order submission & management over WebSocket
- [ ] Retail Trader agent (`RetailTrader.py`) — simulated market participant
- [ ] Bloomberg-style frontend dashboard (`bloomberg/index.html`)
- [ ] Market order support (in addition to limit orders)
- [ ] Cancel-on-disconnect for open orders tied to a WebSocket session
- [ ] Multi-instrument support (multiple symbols)
- [ ] FIX protocol adapter

---

##  License

MIT License. See [LICENSE](./LICENSE) for details.