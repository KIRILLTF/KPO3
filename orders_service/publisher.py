import asyncio
import json
import aio_pika
from database import database
from models import outbox
from config import settings

async def start_publisher():
    await asyncio.sleep(1)
    conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    chan = await conn.channel()

    # Гарантируем, что очередь payment_requests существует
    await chan.declare_queue("payment_requests", durable=True)

    while True:
        rows = await database.fetch_all(
            outbox.select().where(outbox.c.processed == False)
        )
        for row in rows:
            msg = aio_pika.Message(
                body=json.dumps(row["payload"]).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await chan.default_exchange.publish(
                msg,
                routing_key="payment_requests"
            )
            await database.execute(
                outbox.update()
                      .where(outbox.c.id == row["id"])
                      .values(processed=True)
            )
        await asyncio.sleep(1)
