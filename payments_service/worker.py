import asyncio, json, aio_pika
from database import database
from models import inbox, outbox, accounts
from config import settings


async def start_worker():
    await asyncio.sleep(1)
    conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    chan = await conn.channel()

    await chan.declare_queue("payment_requests", durable=True)
    await chan.declare_queue("payment_results", durable=True)

    q = await chan.declare_queue("payment_requests", durable=True)

    async with q.iterator() as it:
        async for msg in it:
            async with msg.process():
                data = json.loads(msg.body)
                msg_id = str(data["order_id"])

                # идемпотентность
                if await database.fetch_one(
                    inbox.select().where(inbox.c.msg_id == msg_id)
                ):
                    continue

                await database.execute(
                    inbox.insert().values(
                        msg_id=msg_id,
                        payload=data,
                        processed=True,
                    )
                )

                acct = await database.fetch_one(
                    accounts.select().where(accounts.c.user_id == data["user_id"])
                )
                if not acct or acct["balance"] < data["amount"]:
                    success = False
                else:
                    new_balance = acct["balance"] - data["amount"]
                    await database.execute(
                        accounts.update()
                        .where(accounts.c.user_id == data["user_id"])
                        .values(balance=new_balance)
                    )
                    success = True

                result = {"order_id": data["order_id"], "success": success}

                # кладём в outbox с processed=False
                await database.execute(
                    outbox.insert().values(payload=result, processed=False)
                )

                # публикуем результат
                await chan.default_exchange.publish(
                    aio_pika.Message(body=json.dumps(result).encode()),
                    routing_key="payment_results",
                )