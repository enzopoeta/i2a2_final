# Dead Letter Queue (DLQ) - Taxes Service

## Visão Geral

O **Taxes Service** implementa um mecanismo de **Dead Letter Queue (DLQ)** para gerenciar mensagens que falharam durante o processamento de cálculo de taxas. Este mecanismo garante que mensagens com problemas sejam isoladas e não bloqueiem o processamento de mensagens válidas.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      TAXES SERVICE                          │
│                                                             │
│  ┌──────────────┐         ┌──────────────────────┐        │
│  │     API      │────────>│   RabbitMQ Client    │        │
│  │   (FastAPI)  │         │  (Publisher)         │        │
│  └──────────────┘         └──────────┬───────────┘        │
│                                      │                      │
└──────────────────────────────────────┼──────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │     RabbitMQ         │
                            │                      │
                            │  ┌────────────────┐ │
                            │  │ taxes_calculation│ │ ◄─┐
                            │  └────────┬───────┘ │   │
                            │           │          │   │ Requeue
                            │           ▼          │   │ (retry)
┌─────────────────────────┐ │  ┌────────────────┐ │   │
│   TAXES SERVICE         │ │  │ DLQ Worker     │ │   │
│                         │ │  │ (Consumer)     │ │───┘
│  ┌──────────────────┐  │ │  └────────┬───────┘ │
│  │ RabbitMQ Worker  │◄─┼─┤           │          │
│  │   (Consumer)     │  │ │           │          │
│  └────┬─────────────┘  │ │           │ Fail     │
│       │                 │ │           │ (max     │
│       │ Success         │ │           │ retries) │
│       ▼                 │ │           ▼          │
│  ┌──────────────────┐  │ │  ┌────────────────┐ │
│  │ Calculate Taxes  │  │ │  │taxes_calculation│ │
│  │    & Log         │  │ │  │     _dlq        │ │
│  └──────────────────┘  │ │  └────────────────┘ │
└─────────────────────────┘ └──────────────────────┘
```

## Componentes

### 1. Filas RabbitMQ

#### Fila Principal: `taxes_calculation`
- **Propósito**: Recebe notas fiscais para cálculo de taxas
- **Formato**: JSON com estrutura `{nota_fiscal: {...}, items: [...]}`
- **Durável**: Sim (mensagens persistem após restart do RabbitMQ)
- **Processamento**: Consumer consome e processa mensagens uma de cada vez

#### Dead Letter Queue: `taxes_calculation_dlq`
- **Propósito**: Armazena mensagens que falharam após múltiplas tentativas
- **Acionamento**: Mensagem é enviada após atingir `RABBITMQ_MAX_RETRIES`
- **Durável**: Sim
- **Uso**: Para análise posterior e correção manual

### 2. Worker/Consumer

O worker é iniciado automaticamente em background quando o serviço sobe e implementa:

- **Consumo de Mensagens**: Processa mensagens da fila `taxes_calculation`
- **Cálculo de Taxas**: Calcula ICMS e outras taxas baseadas em UF origem/destino, NCM, CFOP
- **Logging Detalhado**: Registra todas as operações e resultados
- **Retry Logic**: Reprocessa mensagens que falharam
- **DLQ Handling**: Envia mensagens que excederam retries para DLQ

## Fluxo de Processamento

### Cenário 1: Processamento Bem-Sucedido ✅

```
1. Mensagem chega na fila taxes_calculation
2. Worker consome a mensagem
3. Processa e calcula as taxas
4. Loga os resultados
5. ACK (acknowledges) a mensagem
6. Mensagem é removida da fila
```

### Cenário 2: Falha Temporária com Retry 🔄

```
1. Mensagem chega na fila taxes_calculation
2. Worker consome a mensagem (tentativa 1/4)
3. Erro ocorre durante processamento
4. Worker incrementa contador de retry (x-retry-count: 1)
5. Worker republica mensagem na fila
6. Worker ACK a mensagem original
7. Processo se repete até sucesso ou max retries
```

### Cenário 3: Falha Permanente - Envio para DLQ 💀

```
1. Mensagem chega na fila taxes_calculation
2. Worker consome a mensagem (tentativa 4/4)
3. Erro ocorre durante processamento
4. Worker detecta que max retries foi atingido
5. Worker publica mensagem na DLQ (taxes_calculation_dlq)
6. Worker ACK a mensagem da fila principal
7. Mensagem permanece na DLQ para análise
```

### Cenário 4: JSON Inválido - DLQ Imediato ⚠️

```
1. Mensagem com JSON malformado chega na fila
2. Worker tenta fazer parse do JSON
3. JSONDecodeError é detectado
4. Worker envia diretamente para DLQ (sem retry)
5. Worker ACK a mensagem
6. Mensagem fica na DLQ com reason: "Invalid JSON format"
```

## Configurações

### Variáveis de Ambiente

```bash
# Fila principal de cálculo de taxas
RABBITMQ_TAXES_QUEUE=taxes_calculation

# Dead Letter Queue para mensagens falhadas
RABBITMQ_TAXES_DLQ=taxes_calculation_dlq

# Número máximo de tentativas antes de enviar para DLQ
RABBITMQ_MAX_RETRIES=3

# Configurações de conexão
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin
```

### Comportamento de Retry

- **Tentativa 1**: Primeira tentativa de processamento
- **Tentativa 2-4**: Retries automáticos após falhas
- **Após 4 tentativas**: Mensagem é enviada para DLQ

## Estrutura de Mensagens

### Mensagem na Fila Principal

```json
{
  "nota_fiscal": {
    "chave_acesso": "35250612345678000199550010000123451234567890",
    "numero_nf": "12345",
    "uf_emitente": "SP",
    "uf_destinatario": "RJ",
    "destino_operacao": "2 - Interestadual",
    "valor_nota_fiscal": 15750.50,
    ...
  },
  "items": [
    {
      "numero_produto": 1,
      "descricao_produto": "Notebook Dell",
      "codigo_ncm_sh": "84713012",
      "cfop": "6102",
      "quantidade": 10.0,
      "valor_total": 35000.00,
      ...
    }
  ]
}
```

### Headers nas Mensagens

```json
{
  "x-retry-count": 2,           // Número de tentativas realizadas
  "x-death-reason": "..."       // Motivo do envio para DLQ (apenas na DLQ)
}
```

## Monitoramento

### Logs do Worker

O worker gera logs detalhados de todas as operações:

```
🚀 Starting RabbitMQ Consumer Worker for Taxes Calculation...
📡 Connecting to RabbitMQ at rabbitmq:5672
📦 Dead Letter Queue 'taxes_calculation_dlq' declared
📦 Main queue 'taxes_calculation' declared
🔁 Max retries configured: 3
👂 Waiting for messages in queue 'taxes_calculation'...

📋 Processing message (attempt 1/4)
================================================================================
 📨 Nova Nota Fiscal Recebida para Cálculo de Taxas 
================================================================================
{
  "nota_fiscal": {...},
  "items": [...]
}
--------------------------------------------------------------------------------
SUMMARY:
  Chave de Acesso: 35250612345678000199550010000123451234567890
  Número NF: 12345
  Emitente: EMPRESA EXEMPLO LTDA
  Destinatário: CLIENTE EXEMPLO SA
  Valor Total: R$ 15750.50
  UF Origem: SP
  UF Destino: RJ
  Número de Itens: 5
================================================================================

🧮 Calculating taxes...
   Processing 5 items
   Origin UF: SP
   Destination UF: RJ
   Operation Type: 2 - Interestadual
✅ Taxes calculated:
   ICMS Rate: 18.0%
   ICMS Value: R$ 2835.09
   Total Taxes: R$ 2835.09

💾 Tax calculation completed successfully
✅ Message processed and acknowledged
================================================================================
```

### Verificar Filas no RabbitMQ Management UI

Acesse: `http://localhost:15672`
- **Usuário**: admin
- **Senha**: admin

**Filas disponíveis:**
- `taxes_calculation` - Fila principal
- `taxes_calculation_dlq` - Dead Letter Queue

**Métricas importantes:**
- Total de mensagens
- Mensagens prontas (Ready)
- Mensagens não confirmadas (Unacked)
- Taxa de mensagens/segundo

### Inspeção da DLQ

Para visualizar mensagens na DLQ via Management UI:

1. Acesse `http://localhost:15672/#/queues`
2. Clique em `taxes_calculation_dlq`
3. Use "Get messages" para visualizar conteúdo
4. Verifique o header `x-death-reason` para entender o motivo da falha

## Recuperação de Mensagens da DLQ

### Opção 1: Republicar Mensagem Manualmente (UI)

1. Acesse Management UI → Queues → `taxes_calculation_dlq`
2. Get messages (pegue a mensagem)
3. Copie o JSON
4. Vá para Queues → `taxes_calculation`
5. Publish message com o JSON copiado

### Opção 2: Script Python para Mover Mensagens

```python
import pika
import json

# Conectar ao RabbitMQ
credentials = pika.PlainCredentials('admin', 'admin')
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost', 5672, '/', credentials)
)
channel = connection.channel()

# Consumir da DLQ
method, properties, body = channel.basic_get(queue='taxes_calculation_dlq', auto_ack=False)

if method:
    # Republicar na fila principal (sem retry count para resetar)
    channel.basic_publish(
        exchange='',
        routing_key='taxes_calculation',
        body=body,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    # Confirmar consumo da DLQ
    channel.basic_ack(delivery_tag=method.delivery_tag)
    print("Mensagem movida da DLQ para fila principal")
else:
    print("Nenhuma mensagem na DLQ")

connection.close()
```

### Opção 3: Via API do Taxes Service

Se você corrigiu o problema (dados no banco, serviço externo, etc), pode simplesmente reprocessar a nota fiscal fazendo uma nova requisição:

```bash
curl -X POST http://localhost:8002/calculate-taxes/ \
  -H "Content-Type: application/json" \
  -d '{"chave_acesso": "35250612345678000199550010000123451234567890"}'
```

Isso buscará a nota fiscal do banco e republicará na fila.

## Tipos de Erros e Como Tratá-los

### 1. JSON Inválido (Sem Retry)
**Causa**: Mensagem malformada ou corrompida  
**Ação**: Vai direto para DLQ  
**Solução**: Inspecionar mensagem, corrigir formato, republicar

### 2. Erro de Processamento (Com Retry)
**Causa**: Exceção durante cálculo de taxas  
**Ação**: Retry até 3 vezes  
**Solução**: Verificar logs, corrigir lógica de cálculo, aguardar retry

### 3. Timeout ou Erro de Conexão (Com Retry)
**Causa**: Serviço externo indisponível  
**Ação**: Retry automático  
**Solução**: Aguardar serviço voltar, mensagem será reprocessada

### 4. Dados Inválidos no Banco (Com Retry)
**Causa**: Nota fiscal com dados inconsistentes  
**Ação**: Retry até DLQ  
**Solução**: Corrigir dados no banco, republicar da DLQ

## Best Practices

### 1. Monitoramento Ativo
- Configure alertas para mensagens na DLQ
- Monitore taxa de erro
- Revise logs regularmente

### 2. Análise da DLQ
- Revisar DLQ diariamente
- Categorizar tipos de erros
- Identificar padrões de falhas

### 3. Correção Proativa
- Corrigir causas raiz dos erros
- Melhorar validações de dados
- Adicionar testes para casos de erro

### 4. Documentação
- Documentar todos os casos de erro encontrados
- Manter registro de soluções aplicadas
- Atualizar processos baseado em aprendizados

## Comandos Úteis

### Verificar Status das Filas
```bash
# Ver quantidade de mensagens
docker exec -it rabbitmq rabbitmqctl list_queues

# Ver detalhes de uma fila específica
docker exec -it rabbitmq rabbitmqctl list_queues name messages consumers
```

### Logs do Service
```bash
# Ver logs do taxes-service
docker compose logs -f taxes-service

# Ver apenas últimas 100 linhas
docker compose logs --tail=100 taxes-service

# Filtrar erros
docker compose logs taxes-service | grep "ERROR"
```

### Purgar Filas (CUIDADO!)
```bash
# Limpar fila principal
docker exec -it rabbitmq rabbitmqctl purge_queue taxes_calculation

# Limpar DLQ
docker exec -it rabbitmq rabbitmqctl purge_queue taxes_calculation_dlq
```

## Troubleshooting

### Problema: Mensagens não estão sendo consumidas

**Sintomas**: Mensagens acumulando na fila  
**Possíveis Causas**:
- Worker não está rodando
- Erro crítico no worker que impede consumo
- Connection timeout

**Solução**:
```bash
# Verificar se worker está ativo
docker compose logs taxes-service | grep "Starting RabbitMQ Consumer"

# Reiniciar serviço
docker compose restart taxes-service

# Verificar conexão com RabbitMQ
docker compose logs taxes-service | grep "RabbitMQ"
```

### Problema: Todas as mensagens indo para DLQ

**Sintomas**: DLQ crescendo rapidamente  
**Possíveis Causas**:
- Bug no código de processamento
- Configuração incorreta
- Dados inválidos em todas as mensagens

**Solução**:
```bash
# Parar consumidor temporariamente
docker compose stop taxes-service

# Analisar logs de erro
docker compose logs taxes-service | grep "ERROR"

# Inspecionar uma mensagem da DLQ
# Via UI: http://localhost:15672

# Corrigir problema e reiniciar
docker compose start taxes-service
```

### Problema: Worker travado

**Sintomas**: Worker não processa novas mensagens  
**Possíveis Causas**:
- Processamento demorado
- Deadlock
- Connection perdida

**Solução**:
```bash
# Verificar última atividade
docker compose logs --tail=50 taxes-service

# Reiniciar serviço
docker compose restart taxes-service
```

## Considerações de Performance

- **QoS Setting**: `prefetch_count=1` - Processa uma mensagem por vez
- **Mensagens Persistentes**: Delivery mode = 2 (Persistent)
- **Manual ACK**: Garante que mensagens não sejam perdidas
- **Retry Strategy**: Exponential backoff pode ser implementado no futuro

## Roadmap

Melhorias futuras planejadas:

1. **Exponential Backoff**: Aumentar delay entre retries
2. **Metrics**: Prometheus metrics para DLQ e taxa de sucesso
3. **Auto-recovery**: Script automático para reprocessar DLQ
4. **Alerting**: Integração com sistemas de alerta (Slack, email)
5. **Dashboard**: Grafana dashboard para visualização de métricas

