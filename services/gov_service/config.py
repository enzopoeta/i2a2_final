import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_PORT = int(os.getenv('SERVICE_PORT', '8003'))

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

CNPJ_API_URLS = [
    "https://open.cnpja.com/office/{cnpj}",
    "https://publica.cnpj.ws/cnpj/{cnpj}"
]
