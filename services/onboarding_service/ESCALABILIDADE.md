# Escalabilidade Horizontal - Onboarding Service

## Visão Geral

O **Onboarding Service** suporta **escalabilidade horizontal** nativamente através do padrão **Work Queue** do RabbitMQ. Múltiplas instâncias podem rodar simultaneamente sem consumir mensagens em duplicata.

## Configuração Atual

### Garantias de Não-Duplicação

```python
# onboarding_service/rabbitmq_worker.py

# 1. QoS com prefetch_count=1
channel.basic_qos(prefetch_count=1)

# 2. Manual acknowledgment
channel.basic_consume(
    queue=RABBITMQ_QUEUE,
    on_message_callback=process_message,
    auto_ack=False  # ← Garante processamento sem duplicação
)

# 3. ACK apenas após sucesso
ch.basic_ack(delivery_tag=method.delivery_tag)
```

## Como Escalar

### Docker Compose

```bash
# Escalar para 3 instâncias
docker compose up -d --scale onboarding-service=3

# Verificar instâncias
docker compose ps onboarding-service

# Ver logs de todas as instâncias
docker compose logs -f onboarding-service
```

### Verificar Distribuição de Carga

```bash
# Via RabbitMQ Management UI
# http://localhost:15672
# Queues → notas_fiscais → Consumers

# Via CLI
docker exec -it rabbitmq rabbitmqctl list_consumers
docker exec -it rabbitmq rabbitmqctl list_queues name messages consumers
```

## Fluxo com Múltiplas Instâncias

```
                              ┌─────────────────────┐
                              │     RabbitMQ        │
                              │                     │
                              │  ┌───────────────┐  │
                        ┌────>│  │ notas_fiscais │  │
                        │     │  └───────┬───────┘  │
┌──────────┐            │     │          │          │
│Load      │────────────┘     └──────────┼──────────┘
│Service   │                             │ Round-Robin
└──────────┘                             │
                        ┌────────────────┼────────────────┐
                        │                │                │
                        ▼                ▼                ▼
                  ┌──────────┐    ┌──────────┐    ┌──────────┐
                  │Onboarding│    │Onboarding│    │Onboarding│
                  │  Inst 1  │    │  Inst 2  │    │  Inst 3  │
                  └─────┬────┘    └─────┬────┘    └─────┬────┘
                        │                │                │
                        ▼                ▼                ▼
                  ┌──────────┐    ┌──────────┐    ┌──────────┐
                  │   N8N    │    │   N8N    │    │   N8N    │
                  │Classifier│    │Classifier│    │Classifier│
                  └─────┬────┘    └─────┬────┘    └─────┬────┘
                        │                │                │
                        ▼                ▼                ▼
                  ┌──────────────────────────────────────┐
                  │         PostgreSQL Database          │
                  └──────────────────────────────────────┘
```

## Testes de Carga

```bash
# Script de teste (enviar 100 notas fiscais)
for i in {1..100}; do
  curl -X POST http://localhost:8001/insert-nota-fiscal/ \
    -F "file=@exemplo_nota_fiscal.json" &
done
wait

# Monitorar processamento
docker compose logs -f onboarding-service | grep "Message processed"
```

## Mesma Implementação do Taxes Service

Ambos os serviços usam **exatamente o mesmo padrão**:

| Característica | Implementação |
|----------------|---------------|
| QoS | `prefetch_count=1` |
| ACK | Manual (`auto_ack=False`) |
| Fila | Única, compartilhada |
| Distribuição | Round-robin automático |
| Duplicação | ❌ Impossível |

**Conclusão**: Sistema já está pronto para escalabilidade horizontal! 🎉

Para mais detalhes, veja: [Taxes Service - ESCALABILIDADE.md](../../taxes_service/ESCALABILIDADE.md)

