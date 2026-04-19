import asyncio
import random
import time
import uuid

from OrderBook import OrderBook, Order
from OrderServer import OrderServer
from MarketDataServer import MarketDataServer


async def simulate_market(order_book: OrderBook, num_orders: int = 2000, mean_interval: float = 0.3):
    """Generate a stream of random limit orders to keep the market alive."""
    last_price = 100.0
    order_count = 0

    while order_count < num_orders:
        await asyncio.sleep(random.expovariate(1.0 / mean_interval))

        # 10% chance: cancel a random open order
        if random.random() < 0.10 and order_book.order_map:
            order_id = random.choice(list(order_book.order_map.keys()))
            await order_book.cancel_order(order_id)
            continue

        side = random.choice(["buy", "sell"])
        # Price walk around last trade price
        ref = order_book.last_trade_price or last_price
        price = round(ref + random.gauss(0, 0.5), 2)
        price = max(price, 0.01)
        quantity = random.randint(1, 10)
        trader_id = f"trader{random.randint(1, 50)}"

        order = Order(
            order_id=str(uuid.uuid4()),
            trader_id=trader_id,
            side=side,
            price=price,
            quantity=quantity,
            timestamp=time.time(),
        )

        try:
            await order_book.add_order(order)
        except Exception:
            pass

        order_count += 1


async def main():
    order_book = OrderBook()

    order_server = OrderServer(order_book, host="127.0.0.1", port=8765)
    market_data_server = MarketDataServer(order_book, host="127.0.0.1", port=8766)

    print("=" * 50)
    print("  LOB Simulator starting up…")
    print("  Order Server  → ws://127.0.0.1:8765")
    print("  Market Data   → ws://127.0.0.1:8766")
    print("  Bloomberg UI  → open simulator/bloomberg/index.html")
    print("=" * 50)

    await asyncio.gather(
        order_server.start(),
        market_data_server.start(),
        simulate_market(order_book),
    )


if __name__ == "__main__":
    asyncio.run(main())