# Taxes Service

Serviço responsável por buscar notas fiscais do banco de dados e enviá-las para uma fila exclusiva de cálculo de taxas no RabbitMQ.

## Funcionalidades

- **API REST** para processar notas fiscais
- **Busca nota fiscal completa** (cabeçalho + itens) do banco de dados PostgreSQL
- **Conversão para formato JSON** padronizado usado no sistema
- **Publicação em fila RabbitMQ** exclusiva para cálculo de taxas

## Endpoints

### Health Check
```
GET /health
```
Retorna o status de saúde do serviço.

**Resposta:**
```json
{
  "status": "healthy",
  "service": "taxes_service"
}
```

### Status Check
```
GET /status
```
Retorna status detalhado com estatísticas do banco de dados.

**Resposta:**
```json
{
  "status": "online",
  "service": "taxes_service",
  "version": "1.0.0",
  "notas_fiscais": 150,
  "itens_nota_fiscal": 450
}
```

### Calcular Taxas
```
POST /calculate-taxes/
Content-Type: application/json

{
  "chave_acesso": "35250612345678000199550010000123451234567890"
}
```

Busca a nota fiscal do banco de dados pela chave de acesso e envia para a fila de cálculo de taxas.

**Request Body:**
```json
{
  "chave_acesso": "string (44 caracteres)"
}
```

**Resposta de Sucesso (200):**
```json
{
  "message": "Nota fiscal sent to taxes calculation queue successfully",
  "chave_acesso": "35250612345678000199550010000123451234567890",
  "numero_nf": "12345",
  "razao_social_emitente": "EMPRESA EXEMPLO LTDA",
  "nome_destinatario": "CLIENTE EXEMPLO SA",
  "items_count": 5,
  "valor_total": 15750.50,
  "classificacao": "Materiais de Escritório"
}
```

**Resposta de Erro (404):**
```json
{
  "detail": "Nota fiscal not found with chave_acesso: ..."
}
```

**Resposta de Erro (400):**
```json
{
  "detail": "chave_acesso is required and cannot be empty"
}
```

**Resposta de Erro (500):**
```json
{
  "detail": "Failed to publish nota fiscal to taxes calculation queue"
}
```

## Formato do JSON Enviado para a Fila

O serviço busca a nota fiscal completa do banco de dados e converte para o formato JSON usado no sistema:

```json
{
  "nota_fiscal": {
    "chave_acesso": "35250612345678000199550010000123451234567890",
    "modelo": "55 - NF-E EMITIDA EM SUBSTITUIÇÃO AO MODELO 1 OU 1A",
    "serie_nf": "1",
    "numero_nf": "12345",
    "natureza_operacao": "Venda de Mercadoria",
    "data_emissao": "2025-06-15",
    "evento_mais_recente": "Nota Fiscal Autorizada",
    "data_hora_evento_mais_recente": "2025-06-15 10:30:00",
    "cpf_cnpj_emitente": "12345678000199",
    "razao_social_emitente": "EMPRESA EXEMPLO LTDA",
    "inscricao_estadual_emitente": "123456789",
    "uf_emitente": "SP",
    "municipio_emitente": "São Paulo",
    "cnpj_destinatario": "98765432000188",
    "nome_destinatario": "CLIENTE EXEMPLO SA",
    "uf_destinatario": "RJ",
    "indicador_ie_destinatario": "1 - Contribuinte ICMS",
    "destino_operacao": "2 - Interestadual",
    "consumidor_final": "0 - Não",
    "presenca_comprador": "1 - Operação presencial",
    "valor_nota_fiscal": 15750.50,
    "classificacao": "Materiais de Escritório"
  },
  "items": [
    {
      "chave_acesso_nf": "35250612345678000199550010000123451234567890",
      "modelo": "55 - NF-E EMITIDA EM SUBSTITUIÇÃO AO MODELO 1 OU 1A",
      "serie_nf": "1",
      "numero_nf": "12345",
      "natureza_operacao": "Venda de Mercadoria",
      "data_emissao": "2025-06-15",
      "cpf_cnpj_emitente": "12345678000199",
      "razao_social_emitente": "EMPRESA EXEMPLO LTDA",
      "inscricao_estadual_emitente": "123456789",
      "uf_emitente": "SP",
      "municipio_emitente": "São Paulo",
      "cnpj_destinatario": "98765432000188",
      "nome_destinatario": "CLIENTE EXEMPLO SA",
      "uf_destinatario": "RJ",
      "indicador_ie_destinatario": "1 - Contribuinte ICMS",
      "destino_operacao": "2 - Interestadual",
      "consumidor_final": "0 - Não",
      "presenca_comprador": "1 - Operação presencial",
      "numero_produto": 1,
      "descricao_produto": "Notebook Dell Inspiron 15 3000, Intel Core i5, 8GB RAM, 256GB SSD",
      "codigo_ncm_sh": "84713012",
      "ncm_sh_tipo_produto": "Computadores Portáteis",
      "cfop": "6102",
      "quantidade": 10.0,
      "unidade": "UN",
      "valor_unitario": 3500.00,
      "valor_total": 35000.00
    }
  ]
}
```

## Configuração

O serviço é configurado através de variáveis de ambiente:

### Banco de Dados
- `DB_USER`: Usuário do PostgreSQL (default: postgres)
- `DB_PASSWORD`: Senha do PostgreSQL (default: postgres)
- `DB_HOST`: Host do PostgreSQL (default: db)
- `DB_PORT`: Porta do PostgreSQL (default: 5432)
- `DB_NAME`: Nome do banco de dados (default: notasfiscais)

### RabbitMQ
- `RABBITMQ_HOST`: Host do RabbitMQ (default: rabbitmq)
- `RABBITMQ_PORT`: Porta do RabbitMQ (default: 5672)
- `RABBITMQ_USER`: Usuário do RabbitMQ (default: admin)
- `RABBITMQ_PASS`: Senha do RabbitMQ (default: admin)
- `RABBITMQ_TAXES_QUEUE`: Nome da fila de cálculo de taxas (default: taxes_calculation)

### Serviço
- `SERVICE_PORT`: Porta do serviço (default: 8002)

## Como Executar

### Com Docker Compose

```bash
# Iniciar todos os serviços
docker compose up -d

# Verificar logs do taxes-service
docker compose logs -f taxes-service

# Rebuild forçado (se necessário)
docker compose build --no-cache taxes-service
docker compose up -d taxes-service
```

O serviço estará disponível em: `http://localhost:8002`

### Localmente

```bash
cd services/taxes_service

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export DB_HOST=localhost
export RABBITMQ_HOST=localhost
# ... outras variáveis

# Executar
python main.py
```

## Testes

### Testar endpoint de health
```bash
curl http://localhost:8002/health
```

### Testar endpoint de status
```bash
curl http://localhost:8002/status
```

### Enviar nota fiscal para cálculo de taxas
```bash
curl -X POST http://localhost:8002/calculate-taxes/ \
  -H "Content-Type: application/json" \
  -d '{"chave_acesso": "35250612345678000199550010000123451234567890"}'
```

## Fluxo de Processamento

1. **Recebe requisição** POST em `/calculate-taxes/` com `chave_acesso`
2. **Busca nota fiscal** completa no banco de dados (tabelas `notasfiscais` e `itensnotafiscal`)
3. **Converte para JSON** no formato padronizado do sistema
4. **Publica na fila RabbitMQ** `taxes_calculation`
5. **Retorna resposta** com resumo da operação

## RabbitMQ Queue

- **Nome da Fila**: `taxes_calculation`
- **Tipo**: Durable (persistente)
- **Formato**: JSON com `nota_fiscal` e `items`
- **Content-Type**: `application/json`
- **Delivery Mode**: Persistent

## Dependências

- FastAPI 0.104.1
- Uvicorn 0.24.0
- asyncpg 0.29.0 (PostgreSQL async)
- pika 1.3.2 (RabbitMQ)
- python-dotenv 1.0.0

## Logs

O serviço gera logs detalhados de todas as operações:

```
📋 Received taxes calculation request for: 35250612345678000199550010000123451234567890
🔍 Step 1: Retrieving nota fiscal from database...
✅ Found nota fiscal: 12345
   Emitente: EMPRESA EXEMPLO LTDA
   Destinatário: CLIENTE EXEMPLO SA
   Items: 5
   Valor Total: R$ 15750.50
📤 Step 2: Publishing to taxes calculation queue...
📤 Published nota fiscal to taxes queue: 35250612345678000199550010000123451234567890
   Queue: taxes_calculation
   Items: 5
✅ Successfully sent to taxes calculation queue
```

## Arquitetura

```
┌─────────────────┐
│  Client/API     │
└────────┬────────┘
         │ POST /calculate-taxes/
         │ {"chave_acesso": "..."}
         ▼
┌─────────────────────────────┐
│    Taxes Service (API)      │
│  - Valida requisição        │
│  - Busca nota no DB         │
│  - Converte para JSON       │
│  - Publica no RabbitMQ      │
└─────┬──────────────┬────────┘
      │              │
      ▼              ▼
┌──────────┐  ┌─────────────────┐
│PostgreSQL│  │    RabbitMQ     │
│  (Read)  │  │ taxes_calculation│
└──────────┘  └────────┬────────┘
                       │
                       │ Round-robin
                       │ Distribution
              ┌────────┼────────┐
              ▼        ▼        ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │Worker 1│ │Worker 2│ │Worker N│
         │(Inst 1)│ │(Inst 2)│ │(Inst N)│
         └────────┘ └────────┘ └────────┘
         
         🔄 Escalável Horizontalmente
```

### Escalabilidade

O serviço suporta **múltiplas instâncias** rodando simultaneamente:
- ✅ **Sem duplicação**: RabbitMQ distribui mensagens (round-robin)
- ✅ **Load balancing automático**: Cada mensagem vai para um worker
- ✅ **Tolerância a falhas**: Se um worker cai, outro assume

```bash
# Escalar para 5 instâncias
docker compose up -d --scale taxes-service=5
```

📖 **Documentação completa**: [ESCALABILIDADE.md](ESCALABILIDADE.md)

