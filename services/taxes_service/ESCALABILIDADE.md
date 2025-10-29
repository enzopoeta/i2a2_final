# Escalabilidade Horizontal - Taxes Service

## Visão Geral

O **Taxes Service** foi projetado para suportar **escalabilidade horizontal**, permitindo que múltiplas instâncias do serviço rodem simultaneamente sem consumir mensagens em duplicata. O RabbitMQ gerencia automaticamente a distribuição de mensagens entre os consumidores usando o padrão **Work Queue**.

## Como Funciona

### Modelo Work Queue do RabbitMQ

O RabbitMQ implementa nativamente o padrão de **Work Queue (Fila de Trabalho)**, onde:

1. **Uma única fila** contém as mensagens
2. **Múltiplos consumidores** (workers) conectam-se à mesma fila
3. **RabbitMQ distribui** as mensagens usando algoritmo **round-robin**
4. **Cada mensagem** é entregue a **APENAS UM consumidor**
5. **Sem duplicação** de processamento

```
                              ┌─────────────────────┐
                              │     RabbitMQ        │
                              │                     │
                              │  ┌───────────────┐  │
                        ┌────>│  │taxes_calculation│  │
                        │     │  └───────┬───────┘  │
                        │     │          │          │
┌──────────┐            │     └──────────┼──────────┘
│Publisher │────────────┘                │
│  (API)   │                             │ Round-Robin Distribution
└──────────┘                             │
                        ┌────────────────┼────────────────┐
                        │                │                │
                        ▼                ▼                ▼
                  ┌──────────┐    ┌──────────┐    ┌──────────┐
                  │ Worker 1 │    │ Worker 2 │    │ Worker 3 │
                  │(Instance)│    │(Instance)│    │(Instance)│
                  └──────────┘    └──────────┘    └──────────┘
                  Msg 1, 4, 7...  Msg 2, 5, 8...  Msg 3, 6, 9...
```

## Configurações Chave

### 1. prefetch_count=1

```python
channel.basic_qos(prefetch_count=1)
```

**O que faz:**
- Limita cada worker a processar **apenas 1 mensagem por vez**
- Worker só recebe próxima mensagem após ACK da anterior
- Garante distribuição justa de carga entre workers

**Benefícios:**
- Workers mais rápidos não ficam sobrecarregados
- Load balancing automático e justo
- Sem workers ociosos enquanto outros estão sobrecarregados

### 2. auto_ack=False (Manual Acknowledgment)

```python
channel.basic_consume(
    queue=RABBITMQ_TAXES_QUEUE,
    on_message_callback=process_message,
    auto_ack=False  # Manual acknowledgment
)
```

**O que faz:**
- Mensagem só é removida da fila após **ACK explícito**
- Se worker falhar, mensagem volta para a fila
- Outro worker pode processar a mensagem

**Benefícios:**
- Garantia de processamento (at-least-once delivery)
- Tolerância a falhas
- Mensagens não são perdidas se worker cair

### 3. Fila Durável

```python
channel.queue_declare(queue=RABBITMQ_TAXES_QUEUE, durable=True)
```

**O que faz:**
- Fila persiste após restart do RabbitMQ
- Mensagens marcadas como persistentes não são perdidas

**Benefícios:**
- Alta disponibilidade
- Recuperação após falhas

## Escalando o Serviço

### Opção 1: Docker Compose Scale

```bash
# Escalar para 3 instâncias
docker compose up -d --scale taxes-service=3

# Verificar instâncias rodando
docker compose ps taxes-service

# Ver logs de todas as instâncias
docker compose logs -f taxes-service
```

### Opção 2: Múltiplos Containers Nomeados

Editar `docker-compose.yml`:

```yaml
services:
  taxes-service-1:
    build:
      context: ./services/taxes_service
    environment:
      - INSTANCE_NAME=taxes-service-1
      # ... outras variáveis
    networks:
      - app-network

  taxes-service-2:
    build:
      context: ./services/taxes_service
    environment:
      - INSTANCE_NAME=taxes-service-2
      # ... outras variáveis
    networks:
      - app-network

  taxes-service-3:
    build:
      context: ./services/taxes_service
    environment:
      - INSTANCE_NAME=taxes-service-3
      # ... outras variáveis
    networks:
      - app-network
```

### Opção 3: Kubernetes (Produção)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taxes-service
spec:
  replicas: 3  # 3 instâncias
  selector:
    matchLabels:
      app: taxes-service
  template:
    metadata:
      labels:
        app: taxes-service
    spec:
      containers:
      - name: taxes-service
        image: taxes-service:latest
        env:
        - name: RABBITMQ_HOST
          value: "rabbitmq"
        - name: RABBITMQ_TAXES_QUEUE
          value: "taxes_calculation"
        # ... outras variáveis
```

## Garantias de Processamento

### ✅ O que É Garantido

1. **Sem Duplicação**: Cada mensagem processada por APENAS um worker
2. **At-Least-Once**: Mensagem será processada pelo menos uma vez
3. **Ordem na Fila**: FIFO (First In, First Out) dentro da fila
4. **Fairness**: Carga distribuída igualmente entre workers

### ⚠️ O que NÃO É Garantido

1. **Ordem Global**: Com múltiplos workers, ordem de conclusão pode variar
2. **Exactly-Once**: Em caso de falha após processamento mas antes do ACK, pode reprocessar

## Exemplos Práticos

### Cenário 1: 10 Mensagens, 1 Worker

```
Tempo: 10s por mensagem
Total: 100s (10 mensagens × 10s)

Worker 1: Msg1 → Msg2 → Msg3 → Msg4 → Msg5 → Msg6 → Msg7 → Msg8 → Msg9 → Msg10
```

### Cenário 2: 10 Mensagens, 3 Workers

```
Tempo: 10s por mensagem
Total: ~40s (distribuído entre 3 workers)

Worker 1: Msg1 → Msg4 → Msg7 → Msg10
Worker 2: Msg2 → Msg5 → Msg8
Worker 3: Msg3 → Msg6 → Msg9
```

**Ganho de Performance: 60% mais rápido! (100s → 40s)**

### Cenário 3: Worker Falha Durante Processamento

```
1. Worker 2 recebe Msg5
2. Worker 2 começa processamento
3. Worker 2 FALHA antes de dar ACK
4. RabbitMQ detecta desconexão
5. RabbitMQ recoloca Msg5 na fila
6. Worker 1 ou 3 recebe e processa Msg5
```

## Monitoramento de Múltiplas Instâncias

### 1. Via RabbitMQ Management UI

Acesse: `http://localhost:15672`

**Informações disponíveis:**
- Número de consumidores conectados à fila
- Taxa de mensagens/segundo por consumidor
- Mensagens pendentes (ready)
- Mensagens não confirmadas (unacked)

```
Queues → taxes_calculation
├── Overview
│   ├── Total consumers: 3
│   ├── Messages ready: 25
│   └── Messages unacked: 3 (1 por worker)
└── Consumers
    ├── Worker 1: prefetch=1, state=running
    ├── Worker 2: prefetch=1, state=running
    └── Worker 3: prefetch=1, state=running
```

### 2. Via Docker Logs

```bash
# Ver logs de todas as instâncias misturadas
docker compose logs -f taxes-service

# Ver logs de uma instância específica
docker logs -f i2a2_final-taxes-service-1
docker logs -f i2a2_final-taxes-service-2

# Filtrar logs de startup
docker compose logs taxes-service | grep "Starting RabbitMQ Consumer"

# Ver quantos workers conectados
docker compose logs taxes-service | grep "Waiting for messages" | wc -l
```

### 3. Via RabbitMQ CLI

```bash
# Listar consumidores de uma fila
docker exec -it rabbitmq rabbitmqctl list_consumers

# Estatísticas da fila
docker exec -it rabbitmq rabbitmqctl list_queues name messages consumers

# Output esperado com 3 workers:
# taxes_calculation    10    3
```

## Estratégias de Escalabilidade

### Auto-Scaling Baseado em Carga

#### Métricas para Monitorar:

1. **Queue Length** (Comprimento da Fila)
   - Se > 100 mensagens: escalar UP
   - Se < 10 mensagens: escalar DOWN

2. **Message Rate** (Taxa de Mensagens)
   - Incoming rate > Processing rate: escalar UP
   - Processing rate >> Incoming rate: escalar DOWN

3. **Worker CPU/Memory**
   - CPU > 80%: escalar UP
   - CPU < 20%: escalar DOWN

#### Exemplo de Auto-Scaling (Kubernetes HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: taxes-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: taxes-service
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: External
    external:
      metric:
        name: rabbitmq_queue_messages_ready
        selector:
          matchLabels:
            queue: taxes_calculation
      target:
        type: Value
        value: "50"
```

## Teste de Escalabilidade

### Script de Teste de Carga

```python
#!/usr/bin/env python3
"""
Script para testar escalabilidade do taxes-service
Envia múltiplas mensagens e monitora processamento
"""

import requests
import time
import concurrent.futures
from datetime import datetime

API_URL = "http://localhost:8002/calculate-taxes/"
CHAVE_ACESSO = "35250612345678000199550010000123451234567890"
NUM_REQUESTS = 100

def send_request(i):
    """Envia uma requisição de cálculo de taxas"""
    start = time.time()
    try:
        response = requests.post(
            API_URL,
            json={"chave_acesso": CHAVE_ACESSO},
            timeout=30
        )
        elapsed = time.time() - start
        return {
            'id': i,
            'status': response.status_code,
            'time': elapsed,
            'success': response.status_code == 200
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            'id': i,
            'status': 'error',
            'time': elapsed,
            'success': False,
            'error': str(e)
        }

def main():
    print(f"🚀 Iniciando teste de carga: {NUM_REQUESTS} requisições")
    print(f"⏰ Início: {datetime.now()}")
    
    start_time = time.time()
    
    # Executar requisições em paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(send_request, range(NUM_REQUESTS)))
    
    total_time = time.time() - start_time
    
    # Análise dos resultados
    successful = sum(1 for r in results if r['success'])
    failed = NUM_REQUESTS - successful
    avg_time = sum(r['time'] for r in results) / NUM_REQUESTS
    
    print(f"\n📊 Resultados:")
    print(f"   Total de requisições: {NUM_REQUESTS}")
    print(f"   Sucesso: {successful} ({successful/NUM_REQUESTS*100:.1f}%)")
    print(f"   Falhas: {failed} ({failed/NUM_REQUESTS*100:.1f}%)")
    print(f"   Tempo total: {total_time:.2f}s")
    print(f"   Tempo médio/req: {avg_time:.2f}s")
    print(f"   Throughput: {NUM_REQUESTS/total_time:.2f} req/s")
    print(f"⏰ Fim: {datetime.now()}")

if __name__ == "__main__":
    main()
```

### Executar Teste

```bash
# Teste com 1 worker
docker compose up -d --scale taxes-service=1
python3 test_load.py

# Teste com 3 workers
docker compose up -d --scale taxes-service=3
python3 test_load.py

# Teste com 5 workers
docker compose up -d --scale taxes-service=5
python3 test_load.py
```

### Resultados Esperados

```
1 Worker:  100 req em ~100s = 1.0 req/s
3 Workers: 100 req em ~35s  = 2.9 req/s (2.9x faster)
5 Workers: 100 req em ~22s  = 4.5 req/s (4.5x faster)
```

## Boas Práticas

### 1. Dimensionamento Correto

```bash
# Regra geral:
# Workers = min(CPU_CORES, EXPECTED_LOAD / AVG_PROCESSING_TIME)

# Exemplo:
# - 4 CPU cores disponíveis
# - 100 msg/min esperadas
# - 10s tempo médio de processamento
# Workers recomendados: 2-4
```

### 2. Monitoramento Contínuo

- Alertas para fila muito cheia (> 1000 mensagens)
- Alertas para consumidores desconectados
- Métricas de throughput e latência

### 3. Graceful Shutdown

Os workers já implementam graceful shutdown:
```python
except KeyboardInterrupt:
    logger.info("\n⚠️  Interrupted by user")
finally:
    if connection and not connection.is_closed:
        connection.close()
```

### 4. Health Checks

```bash
# Verificar se workers estão consumindo
curl http://localhost:8002/health

# Verificar estatísticas
curl http://localhost:8002/status
```

## Limitações e Considerações

### 1. Ordem de Processamento

Com múltiplos workers, **não há garantia de ordem global** de conclusão:
- Msg1 pode terminar depois de Msg3
- Se ordem é crítica, use 1 worker ou implemente sequenciamento

### 2. Sessões e Estado Compartilhado

- Workers devem ser **stateless**
- Não compartilhar estado entre workers
- Usar banco de dados para estado persistente

### 3. Idempotência

Implemente operações **idempotentes**:
- Processar mesma mensagem 2x deve ter mesmo resultado
- Importante para caso de reprocessamento após falha

```python
def calculate_taxes(data):
    """Função idempotente - pode ser chamada múltiplas vezes"""
    chave_acesso = data['nota_fiscal']['chave_acesso']
    
    # Verificar se já foi processado
    if already_processed(chave_acesso):
        logger.info(f"Já processado: {chave_acesso}")
        return get_cached_result(chave_acesso)
    
    # Processar
    result = do_calculation(data)
    
    # Salvar resultado
    save_result(chave_acesso, result)
    
    return result
```

## Comparação: Onboarding Service

O **Onboarding Service** usa exatamente o mesmo padrão:

| Característica | Onboarding Service | Taxes Service |
|----------------|-------------------|---------------|
| Fila Principal | `notas_fiscais` | `taxes_calculation` |
| DLQ | `notas_fiscais_dlq` | `taxes_calculation_dlq` |
| prefetch_count | 1 | 1 |
| auto_ack | False | False |
| Escalável | ✅ Sim | ✅ Sim |
| Load Balance | ✅ Automático | ✅ Automático |

Ambos os serviços podem ser escalados da mesma forma!

## Conclusão

✅ **O mecanismo atual JÁ está correto!**

O RabbitMQ com o padrão **Work Queue** resolve automaticamente:
- ✅ Distribuição de mensagens (round-robin)
- ✅ Sem duplicação de processamento
- ✅ Load balancing automático
- ✅ Tolerância a falhas
- ✅ Fair dispatch com prefetch_count=1

**Não é necessário implementar grupos ou coordenação adicional.**

Basta escalar o número de instâncias:
```bash
docker compose up -d --scale taxes-service=5
```

E o RabbitMQ cuida do resto! 🎉

