import json
import asyncio
import aio_pika
from app.core.config import settings
from app.schemas.event import EventReceived
from app.services.alert_processor import alert_processor
from app.services.cache_service import cache_service
from app.db.session import AsyncSessionLocal
from app import crud
import logging

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
        self.exchange = None
        self.consuming = False

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE_NAME, 
                aio_pika.ExchangeType.DIRECT, 
                durable=True
            )
            self.queue = await self.channel.declare_queue(
                settings.RABBITMQ_QUEUE_NAME, 
                durable=True
            )
            
            # Bind queue to exchange with routing key
            await self.queue.bind(self.exchange, settings.RABBITMQ_ROUTING_KEY)
            
            logger.info("Successfully connected to RabbitMQ and set up consumer")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def start_consuming(self):
        """Start consuming messages from the queue"""
        if not self.queue:
            await self.connect()
        
        try:
            self.consuming = True
            # Set QoS to process one message at a time
            await self.channel.set_qos(prefetch_count=1)
            
            logger.info("Starting to consume messages...")
            await self.queue.consume(self.process_message)
            
            # Keep the consumer running
            while self.consuming:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            self.consuming = False
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming message from RabbitMQ"""
        try:
            async with message.process():
                # Parse the event data
                try:
                    event_data = json.loads(message.body.decode())
                    event = EventReceived(**event_data)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse message body: {e}")
                    # Message will be acknowledged and discarded
                    return
                
                logger.info(f"Processing event {event.id} of type {event.event_type}")
                
                # Create database session
                try:
                    async with AsyncSessionLocal() as db:
                        # Process the event and check if alert should be generated
                        alert_create = await alert_processor.process_event(event, db)
                        
                        if alert_create:
                            # Create and save the alert
                            alert = await crud.alert.create(db=db, obj_in=alert_create)
                            logger.info(f"Created alert {alert.id} for event {event.id}")
                        else:
                            logger.debug(f"No alert generated for event {event.id}")
                except Exception as e:
                    logger.error(f"Database error processing event {event.id}: {e}")
                    # Re-raise to trigger message retry
                    raise
                        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Message will be rejected and requeued
            raise

    async def stop_consuming(self):
        """Stop consuming messages"""
        self.consuming = False
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("Stopped consuming messages")

    async def initialize_authorized_users_cache(self):
        """Load authorized users into cache on startup"""
        try:
            async with AsyncSessionLocal() as db:
                users = await crud.authorized_user.get_all(db)
                user_ids = {user.user_id for user in users}
                await cache_service.set_authorized_users(user_ids)
                logger.info(f"Loaded {len(user_ids)} authorized users into cache")
        except Exception as e:
            logger.error(f"Error initializing authorized users cache: {e}")


rabbitmq_consumer = RabbitMQConsumer()
