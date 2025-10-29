# rabbitmq_client.py
import pika
import json
import logging
import time
from typing import Dict, List

logger = logging.getLogger(__name__)

RABBITMQ_HOST = "rabbitmq"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin"
QUEUE_NAME = "notas_fiscais"


def get_rabbitmq_connection(retries=5, delay=2):
    """Get RabbitMQ connection with retry logic"""
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


def publish_nota_fiscal(nota_fiscal_data: Dict, items_data: List[Dict], impostos_nota: Dict = None, impostos_items: List[Dict] = None) -> bool:
    """
    Publish nota fiscal, its items, and tax data to RabbitMQ queue
    
    Args:
        nota_fiscal_data: Dictionary with nota fiscal header data
        items_data: List of dictionaries with items data
        impostos_nota: Dictionary with tax totals for the nota fiscal
        impostos_items: List of dictionaries with tax data for each item
        
    Returns:
        bool: True if published successfully, False otherwise
    """
    connection = None
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Declare queue (idempotent)
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Create message payload
        message = {
            "nota_fiscal": nota_fiscal_data,
            "items": items_data,
            "impostos_nota": impostos_nota,
            "impostos_items": impostos_items or []
        }
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(message, default=str),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        
        logger.info(f"Published nota fiscal to RabbitMQ: {nota_fiscal_data.get('chave_acesso')}")
        return True
        
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {e}", exc_info=True)
        return False
    finally:
        if connection and not connection.is_closed:
            connection.close()

