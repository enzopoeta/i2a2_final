# rabbitmq_worker.py
import pika
import json
import logging
import asyncio
import sys
import signal

from rabbitmq_client import get_rabbitmq_connection, QUEUE_NAME
from db_utils import load_data_from_xml, create_db_and_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flag to control graceful shutdown
should_stop = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global should_stop
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    should_stop = True


def process_message(ch, method, properties, body):
    """
    Process a single message from RabbitMQ queue
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    global should_stop
    
    if should_stop:
        ch.stop_consuming()
        return
    
    try:
        # Parse message
        message = json.loads(body)
        nota_fiscal_data = message.get('nota_fiscal')
        items_data = message.get('items', [])
        impostos_nota = message.get('impostos_nota')
        impostos_items = message.get('impostos_items', [])
        
        chave_acesso = nota_fiscal_data.get('chave_acesso') if nota_fiscal_data else None
        logger.info(f"Processing nota fiscal: {chave_acesso} with {len(items_data)} items and {len(impostos_items)} tax items")
        
        # Save to database
        asyncio.run(load_data_from_xml(nota_fiscal_data, items_data, impostos_nota, impostos_items))
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Successfully processed and saved nota fiscal: {chave_acesso}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse message JSON: {e}")
        # Reject and don't requeue - malformed messages should not be retried
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Reject and requeue for retry
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    """Start consuming messages from RabbitMQ queue"""
    logger.info("Starting RabbitMQ consumer...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure database structure exists
    try:
        asyncio.run(create_db_and_tables())
        logger.info("Database structure verified/created")
    except Exception as e:
        logger.error(f"Failed to create database structure: {e}")
        sys.exit(1)
    
    # Connect to RabbitMQ
    connection = None
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare queue (idempotent)
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Set QoS - process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=process_message
        )
        
        logger.info(f"Waiting for messages in queue '{QUEUE_NAME}'. Press CTRL+C to exit.")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in consumer: {e}", exc_info=True)
    finally:
        if connection and not connection.is_closed:
            connection.close()
            logger.info("Connection closed")


if __name__ == "__main__":
    start_consumer()

