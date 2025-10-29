# Dead Letter Queue (DLQ) - Sistema de Retries

## 📋 Visão Geral

O `onboarding_service` agora possui um sistema completo de Dead Letter Queue (DLQ) com controle de retries configurável para processar notas fiscais de forma resiliente.

## 🎯 Funcionalidades

### 1. **Fila Principal** (`notas_fiscais`)
- Recebe mensagens do `loader-service`
- Processa notasfiscais enviando para classificação e salvando no banco
- Tenta reprocessar mensagens em caso de falha

### 2. **Dead Letter Queue** (`notas_fiscais_dlq`)
- Armazena mensagens que falharam após número máximo de tentativas
- Preserva informações sobre o motivo da falha
- Permite análise e reprocessamento manual

### 3. **Sistema de Retries**
- Conta automaticamente o número de tentativas
- Usa headers do RabbitMQ para rastreamento (`x-retry-count`)
- Número de tentativas configurável via variável de ambiente

## ⚙️ Configuração

### Variáveis de Ambiente (docker-compose.yml)

```yaml
environment:
  - RABBITMQ_QUEUE=notas_fiscais          # Nome da fila principal
  - RABBITMQ_DLQ=notas_fiscais_dlq        # Nome da Dead Letter Queue
  - RABBITMQ_MAX_RETRIES=3                # Número máximo de tentativas (padrão: 3)
  - CLASSIFICATION_SERVICE_URL=...         # URL do serviço de classificação
```

### Alterando o Número de Retries

Para alterar o número de tentativas, modifique a variável `RABBITMQ_MAX_RETRIES` no `docker-compose.yml`:

```yaml
- RABBITMQ_MAX_RETRIES=5  # Agora tentará 5 vezes antes de enviar para DLQ
```

Depois reinicie o serviço:
```bash
docker compose restart onboarding-service
```

## 🔄 Fluxo de Processamento

### Caso de Sucesso
```
1. Mensagem chega na fila 'notas_fiscais'
2. Worker processa (tentativa 1/4)
3. Envia para serviço de classificação ✓
4. Salva no banco de dados ✓
5. Mensagem é confirmada (ACK)
```

### Caso de Falha Temporária
```
1. Mensagem chega na fila 'notas_fiscais'
2. Worker processa (tentativa 1/4)
3. Erro ao chamar serviço de classificação ✗
4. Mensagem é reenfileirada com counter++
5. Worker processa (tentativa 2/4)
6. Erro persiste ✗
7. Repete até tentativa 3/4
8. Na 4ª tentativa, se falhar novamente:
   → Mensagem é enviada para 'notas_fiscais_dlq'
   → Confirmada na fila principal
```

### Caso de JSON Malformado
```
1. Mensagem com JSON inválido
2. Worker detecta erro de parsing
3. Enviada DIRETAMENTE para DLQ (sem retries)
4. Motivo: "Invalid JSON format"
```

## 📊 Tipos de Erro

### Erros que Acionam Retries:
- `requests.exceptions.RequestException`: Falha ao chamar serviço de classificação
- `Exception`: Erros gerais (ex: falha no banco de dados)

### Erros que Vão Direto para DLQ:
- `json.JSONDecodeError`: JSON malformado ou inválido

## 🔍 Monitoramento

### Ver Mensagens na Fila Principal
```bash
docker exec rabbitmq rabbitmqadmin list queues name messages
```

### Ver Mensagens na DLQ
```bash
docker exec rabbitmq rabbitmqadmin get queue=notas_fiscais_dlq count=10
```

### Purgar DLQ (limpar todas as mensagens)
```bash
docker exec rabbitmq rabbitmqctl purge_queue notas_fiscais_dlq
```

### Ver Logs do Worker
```bash
docker compose logs onboarding-service --tail=50 -f
```

## 📈 Logs de Exemplo

### Processamento com Sucesso
```
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 📋 Processing message (attempt 1/4)
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 📨 Nova Nota Fiscal Recebida do RabbitMQ
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 🔄 Step 1: Sending to classification service...
2025-10-17 01:42:39 - rabbitmq_worker - INFO - ✅ Received classified data from service
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 🔄 Step 2: Saving to database...
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 💾 Successfully saved to database
2025-10-17 01:42:39 - rabbitmq_worker - INFO - ✅ Message processed and acknowledged
```

### Processamento com Retry
```
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 📋 Processing message (attempt 1/4)
2025-10-17 01:42:39 - rabbitmq_worker - ERROR - ❌ Error calling classification service: Connection timeout
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 🔄 Requeuing message (retry 1/3)
...
2025-10-17 01:42:45 - rabbitmq_worker - INFO - 📋 Processing message (attempt 2/4)
```

### Envio para DLQ
```
2025-10-17 01:42:39 - rabbitmq_worker - INFO - 📋 Processing message (attempt 4/4)
2025-10-17 01:42:39 - rabbitmq_worker - ERROR - ❌ Error processing message: HTTPError 500
2025-10-17 01:42:39 - rabbitmq_worker - WARNING - ⚠️  Max retries (3) exceeded
2025-10-17 01:42:39 - rabbitmq_worker - WARNING - 💀 Message sent to DLQ. Reason: Max retries exceeded - HTTPError: 500
```

## 🛠️ Reprocessamento Manual de Mensagens da DLQ

Se você precisa reprocessar mensagens da DLQ:

1. **Inspecionar mensagem:**
```bash
docker exec rabbitmq rabbitmqadmin get queue=notas_fiscais_dlq count=1
```

2. **Mover de volta para fila principal** (via RabbitMQ Management UI):
   - Acesse: http://localhost:15672 (user: admin, pass: admin)
   - Queues → `notas_fiscais_dlq`
   - Move messages → Queue: `notas_fiscais`

## 📝 Melhores Práticas

1. **Monitore a DLQ regularmente** - Mensagens acumuladas indicam problemas recorrentes
2. **Analise os motivos de falha** - Use os headers `x-death-reason` para diagnóstico
3. **Ajuste o número de retries** conforme a necessidade do seu sistema
4. **Configure alertas** quando a DLQ atingir certo volume

## 🔧 Troubleshooting

### Problema: Muitas mensagens na DLQ
**Solução:** Verifique:
- Serviço de classificação está disponível?
- Conexão com banco de dados está estável?
- Logs de erro no worker

### Problema: Retries não estão funcionando
**Solução:** Verifique:
- Variável `RABBITMQ_MAX_RETRIES` está definida corretamente
- Worker foi reiniciado após mudança de configuração

### Problema: DLQ não está sendo criada
**Solução:**
- Verifique logs do worker ao iniciar
- Confirme que `RABBITMQ_DLQ` está configurado
- Verifique permissões do usuário RabbitMQ

## 📚 Referências

- [RabbitMQ Dead Letter Exchanges](https://www.rabbitmq.com/dlx.html)
- [Pika Documentation](https://pika.readthedocs.io/)
- [Message Reliability Patterns](https://www.rabbitmq.com/reliability.html)


