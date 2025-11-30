import logging
from typing import Optional
import aio_pika
from config import settings
from models import TaskEvent, EventType

logger = logging.getLogger(__name__)

class RabbitMQConnection:
    _connection: Optional[aio_pika.Connection] = None
    _channel: Optional[aio_pika.Channel] = None
    
    @classmethod
    async def connect(cls):
        """Establish RabbitMQ connection"""
        try:
            cls._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            cls._channel = await cls._connection.channel()
            logger.info(f"✓ Connected to RabbitMQ: {settings.rabbitmq_host}:{settings.rabbitmq_port}")
            return cls._channel
        except Exception as e:
            logger.error(f"✗ Failed to connect to RabbitMQ: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close RabbitMQ connection"""
        if cls._connection:
            await cls._connection.close()
            logger.info("✓ Disconnected from RabbitMQ")
    
    @classmethod
    async def get_channel(cls) -> aio_pika.Channel:
        """Get RabbitMQ channel"""
        if cls._channel is None:
            await cls.connect()
        return cls._channel

class RabbitMQProducer:
    """Publish events to RabbitMQ"""
    
    EXCHANGE_NAME = "task_events"
    EXCHANGE_TYPE = "topic"
    QUEUE_NAME = "notification_queue"
    BINDING_KEYS = ["task.*"]
    
    @classmethod
    async def initialize(cls):
        """Initialize exchange and queues"""
        channel = await RabbitMQConnection.get_channel()
        
        # Declare exchange
        exchange = await channel.declare_exchange(
            cls.EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.info(f"✓ Exchange '{cls.EXCHANGE_NAME}' declared")
        
        # Declare queue
        queue = await channel.declare_queue(
            cls.QUEUE_NAME,
            durable=True
        )
        logger.info(f"✓ Queue '{cls.QUEUE_NAME}' declared")
        
        # Bind queue to exchange
        for binding_key in cls.BINDING_KEYS:
            await queue.bind(exchange, routing_key=binding_key)
            logger.info(f"✓ Queue bound to exchange with key: {binding_key}")
        
        return exchange
    
    @classmethod
    async def publish_event(cls, event: TaskEvent):
        """Publish task event"""
        try:
            channel = await RabbitMQConnection.get_channel()
            exchange = await channel.get_exchange(cls.EXCHANGE_NAME)
            
            message = aio_pika.Message(
                body=event.to_json().encode(),
                content_type='application/json',
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            routing_key = f"task.{event.event_type.split('.')[1]}"
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f"✓ Published event: {event.event_type} for task {event.task_id}")
        except Exception as e:
            logger.error(f"✗ Failed to publish event: {e}")
            raise

class RabbitMQConsumer:
    """Consume events from RabbitMQ"""
    
    QUEUE_NAME = "notification_queue"
    EXCHANGE_NAME = "task_events"
    BINDING_KEYS = ["task.*"]
    
    @classmethod
    async def setup_queue(cls):
        """Setup consumer queue and bindings"""
        channel = await RabbitMQConnection.get_channel()
        
        # Declare exchange
        exchange = await channel.declare_exchange(
            cls.EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        # Declare queue
        queue = await channel.declare_queue(
            cls.QUEUE_NAME,
            durable=True
        )
        
        # Bind queue to exchange
        for binding_key in cls.BINDING_KEYS:
            await queue.bind(exchange, routing_key=binding_key)
            logger.info(f"✓ Queue bound to {cls.EXCHANGE_NAME} with key: {binding_key}")
        
        return queue, exchange
    
    @classmethod
    async def start_consuming(cls, callback):
        """Start consuming messages from queue"""
        try:
            queue, _ = await cls.setup_queue()
            
            async with queue.iterator() as queue_iter:
                logger.info(f"✓ Started consuming from queue: {cls.QUEUE_NAME}")
                async for message in queue_iter:
                    try:
                        async with message.process():
                            event_data = message.body.decode()
                            event = TaskEvent.from_json(event_data)
                            await callback(event)
                    except Exception as e:
                        logger.error(f"✗ Error processing message: {e}")
                        await message.nack()
        except Exception as e:
            logger.error(f"✗ Failed to consume messages: {e}")
            raise
