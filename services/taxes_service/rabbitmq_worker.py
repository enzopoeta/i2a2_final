# rabbitmq_worker.py
import pika
import json
import logging
import sys
import os
import asyncio
from typing import Dict

from config import (
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS, 
    RABBITMQ_TAXES_QUEUE, RABBITMQ_TAXES_DLQ, RABBITMQ_MAX_RETRIES
)

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
    channel.queue_declare(queue=RABBITMQ_TAXES_DLQ, durable=True)
    logger.info(f"📦 Dead Letter Queue '{RABBITMQ_TAXES_DLQ}' declared")
    
    # Declare main queue
    channel.queue_declare(queue=RABBITMQ_TAXES_QUEUE, durable=True)
    logger.info(f"📦 Main queue '{RABBITMQ_TAXES_QUEUE}' declared")
    
    logger.info(f"🔁 Max retries configured: {RABBITMQ_MAX_RETRIES}")


def send_to_dlq(channel, body, reason="Max retries exceeded"):
    """
    Send message to Dead Letter Queue
    """
    try:
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_TAXES_DLQ,
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
    logger.info(f"  UF Origem: {nota_fiscal.get('uf_emitente', 'N/A')}")
    logger.info(f"  UF Destino: {nota_fiscal.get('uf_destinatario', 'N/A')}")
    logger.info(f"  Número de Itens: {len(items)}")
    
    if items:
        logger.info("")
        logger.info("  Itens:")
        for idx, item in enumerate(items, 1):
            logger.info(f"    {idx}. {item.get('descricao_produto', 'N/A')} - "
                       f"NCM: {item.get('codigo_ncm_sh', 'N/A')} - "
                       f"CFOP: {item.get('cfop', 'N/A')} - "
                       f"Qtd: {item.get('quantidade', 0)} - "
                       f"R$ {item.get('valor_total', 0):.2f}")
    
    logger.info("=" * 80)


def calculate_taxes(data: Dict) -> Dict:
    """
    Calculate taxes for the nota fiscal
    
    This is a placeholder function that would implement the actual tax calculation logic.
    For now, it just logs the data and returns a mock result.
    
    Args:
        data: Nota fiscal data with 'nota_fiscal' and 'items'
        
    Returns:
        Dict with calculated taxes
    """
    nota_fiscal = data.get('nota_fiscal', {})
    items = data.get('items', [])
    
    logger.info("🧮 Calculating taxes...")
    logger.info(f"   Processing {len(items)} items")
    logger.info(f"   Origin UF: {nota_fiscal.get('uf_emitente', 'N/A')}")
    logger.info(f"   Destination UF: {nota_fiscal.get('uf_destinatario', 'N/A')}")
    logger.info(f"   Operation Type: {nota_fiscal.get('destino_operacao', 'N/A')}")
    
    # Mock tax calculation - replace with real logic
    total_value = nota_fiscal.get('valor_nota_fiscal', 0)
    icms_rate = 0.18  # 18% mock ICMS rate
    icms_value = total_value * icms_rate
    
    # Item-level calculations
    items_with_taxes = []
    for item in items:
        item_total = item.get('valor_total', 0)
        item_with_tax = {
            **item,
            'icms_rate': icms_rate,
            'icms_value': item_total * icms_rate
        }
        items_with_taxes.append(item_with_tax)
    
    result = {
        'nota_fiscal': {
            **nota_fiscal,
            'calculated_taxes': {
                'icms_rate': icms_rate,
                'icms_value': icms_value,
                'total_taxes': icms_value
            }
        },
        'items': items_with_taxes
    }
    
    logger.info(f"✅ Taxes calculated:")
    logger.info(f"   ICMS Rate: {icms_rate * 100}%")
    logger.info(f"   ICMS Value: R$ {icms_value:.2f}")
    logger.info(f"   Total Taxes: R$ {icms_value:.2f}")
    
    return result


def process_message(ch, method, properties, body):
    """
    Process a single message from RabbitMQ queue:
    1. Receive nota fiscal from queue
    2. Calculate taxes
    3. Log results (or save to database/send to another service)
    
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
        print_json_pretty(message, "📨 Nova Nota Fiscal Recebida para Cálculo de Taxas")
        
        # Calculate taxes
        logger.info("🔄 Step 1: Calculating taxes...")
        result = calculate_taxes(message)
        
        # Print result
        print_json_pretty(result, "✅ Taxas Calculadas com Sucesso")
        
        # Here you could:
        # - Save results to database
        # - Send to another queue
        # - Call an external API
        # For now, we just log the results
        
        logger.info("💾 Tax calculation completed successfully")
        
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
        
    except Exception as e:
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
                routing_key=RABBITMQ_TAXES_QUEUE,
                body=body,
                properties=new_properties
            )
            
            # Acknowledge the original message
            ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    """Start consuming messages from RabbitMQ queue with DLQ support"""
    logger.info("🚀 Starting RabbitMQ Consumer Worker for Taxes Calculation...")
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
            queue=RABBITMQ_TAXES_QUEUE,
            on_message_callback=process_message,
            auto_ack=False  # Manual acknowledgment
        )
        
        logger.info(f"👂 Waiting for messages in queue '{RABBITMQ_TAXES_QUEUE}'. Press CTRL+C to exit.")
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

