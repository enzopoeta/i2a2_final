# rabbitmq_client.py
import pika
import json
import logging
from typing import Dict

from config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_TAXES_QUEUE

logger = logging.getLogger(__name__)


def get_rabbitmq_connection(retries=5, delay=2):
    """Get RabbitMQ connection with retry logic"""
    import time
    
    for attempt in range(retries):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            logger.info("Successfully connected to RabbitMQ")
            return connection
        except Exception as e:
            logger.warning(f"Failed to connect to RabbitMQ (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def publish_to_taxes_queue(data: Dict) -> bool:
    """
    Publish nota fiscal to taxes calculation queue
    
    Args:
        data: Nota fiscal data (dict with 'nota_fiscal' and 'items')
        
    Returns:
        bool: True if published successfully, False otherwise
    """
    connection = None
    try:
        # Connect to RabbitMQ
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare queue (idempotent operation)
        channel.queue_declare(queue=RABBITMQ_TAXES_QUEUE, durable=True)
        
        # Convert data to JSON
        message = json.dumps(data, ensure_ascii=False, default=str)
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_TAXES_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type='application/json'
            )
        )
        
        logger.info(f"📤 Published nota fiscal to taxes queue: {data['nota_fiscal'].get('chave_acesso')}")
        logger.info(f"   Queue: {RABBITMQ_TAXES_QUEUE}")
        logger.info(f"   Items: {len(data['items'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error publishing to taxes queue: {e}", exc_info=True)
        return False
    finally:
        if connection and not connection.is_closed:
            connection.close()

