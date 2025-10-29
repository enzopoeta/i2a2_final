# Onboarding Service

Serviço responsável pelo onboarding e classificação de notas fiscais.

## Tecnologias

- Python 3.11
- FastAPI
- PostgreSQL
- RabbitMQ
- AsyncPG

## Endpoints

### Health Check
```
GET /health
```
Retorna o status de saúde do serviço.

### Status
```
GET /status
```
Retorna informações sobre o status do serviço.

## Variáveis de Ambiente

- `DB_USER`: Usuário do banco de dados (padrão: postgres)
- `DB_PASSWORD`: Senha do banco de dados (padrão: postgres)
- `DB_HOST`: Host do banco de dados (padrão: db)
- `DB_PORT`: Porta do banco de dados (padrão: 5432)
- `DB_NAME`: Nome do banco de dados (padrão: notasfiscais)
- `RABBITMQ_HOST`: Host do RabbitMQ (padrão: rabbitmq)
- `RABBITMQ_PORT`: Porta do RabbitMQ (padrão: 5672)
- `RABBITMQ_USER`: Usuário do RabbitMQ (padrão: admin)
- `RABBITMQ_PASS`: Senha do RabbitMQ (padrão: admin)
- `SERVICE_PORT`: Porta do serviço (padrão: 8001)

## Desenvolvimento

O serviço roda na porta 8001 por padrão.

### Build
```bash
docker compose build onboarding-service
```

### Run
```bash
docker compose up -d onboarding-service
```

### Logs
```bash
docker compose logs -f onboarding-service
```

