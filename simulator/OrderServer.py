import asyncio
import websockets
import json
import uuid
import time

from OrderBook import Order


class OrderServer:
    def __init__(self, order_book, host="127.0.0.1", port=8765):
        self.order_book = order_book
        self.host = host
        self.port = port

    async def handle_client(self, websocket):
        trader_id = str(uuid.uuid4())[:8]
        print(f"[OrderServer] Client connected: trader_{trader_id}")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    side = data.get("side")
                    price = data.get("price")
                    quantity = data.get("quantity")

                    if side not in ("buy", "sell"):
                        await websocket.send(json.dumps({"status": "error", "reason": "side must be 'buy' or 'sell'"}))
                        continue
                    if not isinstance(price, (int, float)) or price <= 0:
                        await websocket.send(json.dumps({"status": "error", "reason": "price must be a positive number"}))
                        continue
                    if not isinstance(quantity, int) or quantity <= 0:
                        await websocket.send(json.dumps({"status": "error", "reason": "quantity must be a positive integer"}))
                        continue

                    order = Order(
                        order_id=str(uuid.uuid4()),
                        trader_id=f"trader_{trader_id}",
                        side=side,
                        price=float(price),
                        quantity=int(quantity),
                        timestamp=time.time(),
                    )

                    trades = await self.order_book.add_order(order)
                    await websocket.send(json.dumps({
                        "status": "ok",
                        "order_id": order.order_id,
                        "trades_executed": len(trades),
                        "trades": trades,
                    }))

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"status": "error", "reason": "invalid JSON"}))
                except Exception as e:
                    await websocket.send(json.dumps({"status": "error", "reason": str(e)}))
        finally:
            print(f"[OrderServer] Client disconnected: trader_{trader_id}")

    async def start(self):
        server = await websockets.serve(self.handle_client, self.host, self.port)
        print(f"Order server running on ws://{self.host}:{self.port}")
        await server.wait_closed()