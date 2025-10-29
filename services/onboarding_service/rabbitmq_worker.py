# rabbitmq_worker.py
import pika
import json
import logging
import sys
import os
import requests
import asyncio
from typing import Dict

from config import (
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, 
    RABBITMQ_QUEUE, RABBITMQ_DLQ, RABBITMQ_MAX_RETRIES,
    CLASSIFICATION_SERVICE_URL
)
from db_utils import insert_nota_fiscal_from_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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


def setup_queues(channel):
    """
    Setup main queue and Dead Letter Queue (DLQ)
    """
    # Declare DLQ (where failed messages go after max retries)
    channel.queue_declare(queue=RABBITMQ_DLQ, durable=True)
    logger.info(f"📦 Dead Letter Queue '{RABBITMQ_DLQ}' declared")
    
    # Declare main queue
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    logger.info(f"📦 Main queue '{RABBITMQ_QUEUE}' declared")
    
    logger.info(f"🔁 Max retries configured: {RABBITMQ_MAX_RETRIES}")


def send_to_dlq(channel, body, reason="Max retries exceeded"):
    """
    Send message to Dead Letter Queue
    """
    try:
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_DLQ,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                headers={'x-death-reason': reason}
            )
        )
        logger.warning(f"💀 Message sent to DLQ. Reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to DLQ: {e}")
        return False


def print_json_pretty(data: Dict, title: str = "Received Message"):
    """Print JSON data in a formatted way"""
    logger.info("=" * 80)
    logger.info(f" {title} ")
    logger.info("=" * 80)
    
    # Print the entire JSON structure
    formatted_json = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    logger.info(formatted_json)
    
    # Print summary
    nota_fiscal = data.get('nota_fiscal', {})
    items = data.get('items', [])
    
    logger.info("-" * 80)
    logger.info("SUMMARY:")
    logger.info(f"  Chave de Acesso: {nota_fiscal.get('chave_acesso', 'N/A')}")
    logger.info(f"  Número NF: {nota_fiscal.get('numero_nf', 'N/A')}")
    logger.info(f"  Emitente: {nota_fiscal.get('razao_social_emitente', 'N/A')}")
    logger.info(f"  Destinatário: {nota_fiscal.get('nome_destinatario', 'N/A')}")
    logger.info(f"  Valor Total: R$ {nota_fiscal.get('valor_nota_fiscal', 0):.2f}")
    logger.info(f"  Classificação: {nota_fiscal.get('classificacao', 'Não classificada')}")
    logger.info(f"  Número de Itens: {len(items)}")
    
    if items:
        logger.info("")
        logger.info("  Itens:")
        for idx, item in enumerate(items, 1):
            logger.info(f"    {idx}. {item.get('descricao_produto', 'N/A')} - "
                       f"Qtd: {item.get('quantidade', 0)} - "
                       f"R$ {item.get('valor_total', 0):.2f}")
    
    logger.info("=" * 80)


def send_to_classification_service(data: Dict) -> Dict:
    """
    Send nota fiscal to classification service and return classified data
    
    Args:
        data: Nota fiscal data
        
    Returns:
        Classified nota fiscal data
    """
    try:
        logger.info(f"📤 Sending to classification service: {CLASSIFICATION_SERVICE_URL}")
        
        response = requests.post(
            CLASSIFICATION_SERVICE_URL,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30  # 30 seconds timeout
        )
        
        response.raise_for_status()
        classified_data = response.json()
        
        logger.info(f"✅ Received classified data from service")
        logger.info(f"   Classification: {classified_data.get('nota_fiscal', {}).get('classificacao', 'N/A')}")
        
        return classified_data
        
    except requests.exceptions.Timeout:
        logger.error("⏱️  Timeout calling classification service")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 Connection error calling classification service: {e}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error from classification service: {e}")
        logger.error(f"   Response: {e.response.text if e.response else 'N/A'}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error calling classification service: {e}")
        raise


def process_message(ch, method, properties, body):
    """
    Process a single message from RabbitMQ queue:
    1. Receive nota fiscal from queue
    2. Send to classification service
    3. Save classified nota fiscal to database
    
    Implements retry logic with Dead Letter Queue (DLQ)
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    # Get retry count from message headers
    retry_count = 0
    if properties.headers and 'x-retry-count' in properties.headers:
        retry_count = properties.headers['x-retry-count']
    
    logger.info(f"📋 Processing message (attempt {retry_count + 1}/{RABBITMQ_MAX_RETRIES + 1})")
    
    try:
        # Parse message
        message = json.loads(body)
        
        # Print the JSON content
        print_json_pretty(message, "📨 Nova Nota Fiscal Recebida do RabbitMQ")
        
        # Send to classification service
        logger.info("🔄 Step 1: Sending to classification service...")
        classified_data = send_to_classification_service(message)
        
        # Print classified data
        print_json_pretty(classified_data, "🎯 Nota Fiscal Classificada Recebida")
        
        # Save to database
        logger.info("🔄 Step 2: Saving to database...")
        nota_fiscal = classified_data.get('nota_fiscal', {})
        items = classified_data.get('items', [])
        impostos_nota = classified_data.get('impostos_nota')
        impostos_items = classified_data.get('impostos_items')
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(insert_nota_fiscal_from_json(nota_fiscal, items, impostos_nota, impostos_items))
        loop.close()
        
        if success:
            logger.info("💾 Successfully saved to database")
            logger.info(f"   Chave: {nota_fiscal.get('chave_acesso')}")
            logger.info(f"   Classification: {nota_fiscal.get('classificacao')}")
        else:
            logger.error("❌ Failed to save to database")
            raise Exception("Database insertion failed")
        
        # Acknowledge message only after everything succeeds
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("✅ Message processed and acknowledged")
        logger.info("=" * 80)
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse message JSON: {e}")
        logger.error(f"Raw message: {body}")
        # Malformed JSON - send directly to DLQ
        send_to_dlq(ch, body, reason="Invalid JSON format")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except (requests.exceptions.RequestException, Exception) as e:
        logger.error(f"❌ Error processing message: {e}", exc_info=True)
        
        # Check if we've exceeded max retries
        if retry_count >= RABBITMQ_MAX_RETRIES:
            logger.warning(f"⚠️  Max retries ({RABBITMQ_MAX_RETRIES}) exceeded")
            # Send to DLQ
            error_type = type(e).__name__
            send_to_dlq(ch, body, reason=f"Max retries exceeded - {error_type}: {str(e)}")
            # Acknowledge the message to remove it from main queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # Increment retry count and requeue
            new_retry_count = retry_count + 1
            logger.info(f"🔄 Requeuing message (retry {new_retry_count}/{RABBITMQ_MAX_RETRIES})")
            
            # Publish back to queue with incremented retry count
            new_properties = pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                headers={'x-retry-count': new_retry_count}
            )
            
            ch.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=body,
                properties=new_properties
            )
            
            # Acknowledge the original message
            ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    """Start consuming messages from RabbitMQ queue with DLQ support"""
    logger.info("🚀 Starting RabbitMQ Consumer Worker...")
    logger.info(f"📡 Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    
    # Connect to RabbitMQ
    connection = None
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Setup queues (main queue and DLQ)
        setup_queues(channel)
        
        # Set QoS - process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        channel.basic_consume(
            queue=RABBITMQ_QUEUE,
            on_message_callback=process_message,
            auto_ack=False  # Manual acknowledgment
        )
        
        logger.info(f"👂 Waiting for messages in queue '{RABBITMQ_QUEUE}'. Press CTRL+C to exit.")
        logger.info("=" * 80)
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in consumer: {e}", exc_info=True)
    finally:
        if connection and not connection.is_closed:
            connection.close()
            logger.info("🔌 Connection closed")


if __name__ == "__main__":
    start_consumer()

