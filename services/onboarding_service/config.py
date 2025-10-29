# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'notasfiscais')

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'notas_fiscais')
RABBITMQ_DLQ = os.getenv('RABBITMQ_DLQ', 'notas_fiscais_dlq')
RABBITMQ_MAX_RETRIES = int(os.getenv('RABBITMQ_MAX_RETRIES', '3'))

# Service configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '8001'))

# Classification service configuration
CLASSIFICATION_SERVICE_URL = os.getenv('CLASSIFICATION_SERVICE_URL', 'http://localhost:5678/webhook-test/nf-input')

