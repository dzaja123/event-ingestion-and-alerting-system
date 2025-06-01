import json
import aio_pika
from app.core.config import settings
from app.schemas.event import EventRead
import logging


logger = logging.getLogger(__name__)


class MessageQueueService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
            )
            logger.info("Successfully connected to RabbitMQ and declared exchange.")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def publish_event(self, event: EventRead):
        if not self.channel or not self.exchange:
            logger.error("RabbitMQ channel or exchange not initialized. Attempting to reconnect...")
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Failed to reconnect to RabbitMQ: {e}")
                raise ConnectionError("RabbitMQ connection failed, cannot publish event.")

        message_body = event.model_dump_json().encode()
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json"
        )
        try:
            await self.exchange.publish(
                message,
                routing_key=settings.RABBITMQ_ROUTING_KEY
            )
            logger.info(f"Event {event.id} published to RabbitMQ with routing key {settings.RABBITMQ_ROUTING_KEY}")
        except aio_pika.exceptions.AMQPException as e:
            logger.error(f"AMQP error publishing event {event.id}: {e}")
            raise ConnectionError(f"Failed to publish event due to AMQP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing event {event.id} to RabbitMQ: {e}")
            raise

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("RabbitMQ connection closed.")


message_queue_service = MessageQueueService()
