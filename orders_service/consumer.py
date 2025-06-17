import asyncio
import json
import aio_pika
from database import database
from models import orders
from config import settings

async def start_consumer():
    await asyncio.sleep(1)
    conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    chan = await conn.channel()

    # Гарантируем, что очередь payment_results существует
    await chan.declare_queue("payment_results", durable=True)

    q = await chan.declare_queue("payment_results", durable=True)
    async with q.iterator() as it:
        async for msg in it:
            async with msg.process():
                data = json.loads(msg.body)
                status = "FINISHED" if data.get("success") else "CANCELLED"
                await database.execute(
                    orders.update()
                          .where(orders.c.id == data["order_id"])
                          .values(status=status)
                )
