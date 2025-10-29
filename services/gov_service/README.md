# Gov Service

Serviço para consulta de informações governamentais e públicas.

## Funcionalidades

### 1. Consulta de CNPJ

Endpoint para consultar informações de empresas por CNPJ usando APIs públicas.

**Características:**
- ✅ Consulta em 2 APIs públicas diferentes
- ✅ Seleção aleatória da API a ser consultada
- ✅ Fallback automático se a primeira API falhar
- ✅ Validação de CNPJ
- ✅ Limpeza automática de formatação (aceita CNPJ com ou sem pontuação)

## Endpoints

### Health Check
```
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "gov_service"
}
```

### Status Check
```
GET /status
```

**Resposta:**
```json
{
  "status": "online",
  "service": "gov_service",
  "version": "1.0.0",
  "available_apis": [
    "https://open.cnpja.com",
    "https://publica.cnpj.ws"
  ]
}
```

### Consultar CNPJ
```
GET /cnpjinfo/{cnpj}
```

**Parâmetros:**
- `cnpj`: Número do CNPJ (com ou sem formatação)

**Exemplos de uso:**
```bash
# Com formatação
curl http://localhost:8003/cnpjinfo/00.000.000/0001-00

# Sem formatação
curl http://localhost:8003/cnpjinfo/00000000000100

# Exemplo real
curl http://localhost:8003/cnpjinfo/27865757000102
```

**Resposta de Sucesso (200):**
```json
{
  "success": true,
  "cnpj": "27865757000102",
  "source": "https://open.cnpja.com/office/27865757000102",
  "data": {
    "taxId": "27865757000102",
    "updated": "2023-10-15T12:34:56.789Z",
    "company": {
      "id": 278657,
      "name": "MAGAZINE LUIZA S.A.",
      "equity": 1234567890.00,
      "nature": {
        "id": 2046,
        "text": "Sociedade Anônima Aberta"
      },
      "size": {
        "id": 5,
        "acronym": "DEMAIS",
        "text": "Demais"
      }
    },
    "alias": "MAGALU",
    "founded": "1957-11-16",
    "head": true,
    "statusDate": "2005-11-03",
    "status": {
      "id": 2,
      "text": "Ativa"
    },
    "address": {
      "municipality": 3543402,
      "street": "RUA VOLUNTÁRIOS DA FRANCA",
      "number": "1465",
      "district": "CENTRO",
      "city": "Franca",
      "state": "SP",
      "zip": "14400685",
      "country": {
        "id": 1058,
        "name": "Brasil"
      }
    },
    "phones": [
      {
        "area": "16",
        "number": "37119500"
      }
    ],
    "emails": [
      {
        "address": "contato@magazineluiza.com.br",
        "domain": "magazineluiza.com.br"
      }
    ],
    "mainActivity": {
      "id": 4713002,
      "text": "Lojas de departamentos ou magazines"
    }
  }
}
```

**Resposta de Erro - CNPJ Inválido (400):**
```json
{
  "detail": "Invalid CNPJ format. Expected 14 digits, got: 12345"
}
```

**Resposta de Erro - APIs Indisponíveis (503):**
```json
{
  "detail": {
    "message": "All CNPJ APIs are unavailable",
    "cnpj": "27865757000102",
    "errors": {
      "first_api": {
        "url": "https://open.cnpja.com/office/27865757000102",
        "error": "Connection timeout"
      },
      "second_api": {
        "url": "https://publica.cnpj.ws/cnpj/27865757000102",
        "error": "HTTP 429: Too Many Requests"
      }
    }
  }
}
```

## APIs Utilizadas

### 1. Open CNPJA
- **URL**: https://open.cnpja.com/office/{cnpj}
- **Documentação**: https://open.cnpja.com
- **Gratuita**: Sim
- **Limite de requisições**: Consultar documentação

### 2. CNPJ.ws
- **URL**: https://publica.cnpj.ws/cnpj/{cnpj}
- **Documentação**: https://cnpj.ws
- **Gratuita**: Sim
- **Limite de requisições**: Consultar documentação

## Lógica de Fallback

O serviço implementa uma estratégia inteligente para garantir alta disponibilidade:

1. **Randomização**: As APIs são consultadas em ordem aleatória
2. **Fallback Automático**: Se a primeira API falhar, tenta automaticamente a segunda
3. **Logging Detalhado**: Todas as tentativas são logadas para monitoramento
4. **Erro Informativo**: Se ambas falharem, retorna detalhes de ambos os erros

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Gov Service    │
│  /cnpjinfo      │
└────┬────────────┘
     │
     │ Random Order
     ├──────────┬─────────┐
     ▼          ▼         │
┌─────────┐ ┌─────────┐  │
│API 1    │ │API 2    │  │
│CNPJA    │ │CNPJ.ws  │  │
└────┬────┘ └────┬────┘  │
     │           │        │
     │ Success?  │        │
     │ ──No──────┼────────┘
     │           │ Try Second
     │ ─Yes──────┤
     ▼           ▼
   Return     Return
   Data       Data
```

## Como Executar

### Com Docker Compose

```bash
# Build do serviço
docker compose build gov-service

# Iniciar o serviço
docker compose up -d gov-service

# Ver logs
docker compose logs -f gov-service

# Parar o serviço
docker compose stop gov-service
```

### Localmente

```bash
cd services/gov_service

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

O serviço estará disponível em: `http://localhost:8003`

## Testes

### Testar Health Check
```bash
curl http://localhost:8003/health
```

### Testar Status
```bash
curl http://localhost:8003/status
```

### Testar Consulta de CNPJ
```bash
# Magazine Luiza
curl http://localhost:8003/cnpjinfo/27865757000102 | jq .

# Petrobras
curl http://localhost:8003/cnpjinfo/33000167000101 | jq .

# Banco do Brasil
curl http://localhost:8003/cnpjinfo/00000000000191 | jq .
```

### Testar com CNPJ Formatado
```bash
curl http://localhost:8003/cnpjinfo/27.865.757/0001-02 | jq .
```

### Testar CNPJ Inválido
```bash
curl http://localhost:8003/cnpjinfo/123 | jq .
```

## Monitoramento

### Logs do Serviço

```bash
# Ver logs em tempo real
docker compose logs -f gov-service

# Ver últimos 50 logs
docker compose logs --tail=50 gov-service
```

**Exemplo de logs:**
```
gov-service-1  | INFO:__main__:🔍 Fetching CNPJ info for: 27865757000102
gov-service-1  | INFO:__main__:📡 API order: ['https://publica.cnpj.ws/cnpj/27865757000102', 'https://open.cnpja.com/office/27865757000102']
gov-service-1  | INFO:__main__:🌐 Trying first API: https://publica.cnpj.ws/cnpj/27865757000102
gov-service-1  | INFO:__main__:✅ Success with first API: https://publica.cnpj.ws/cnpj/27865757000102
```

## Configuração

### Variáveis de Ambiente

```bash
SERVICE_PORT=8003  # Porta do serviço (default: 8003)
```

## Dependências

- FastAPI 0.104.1
- Uvicorn 0.24.0
- Requests 2.31.0
- Python-dotenv 1.0.0

## Limitações

- **Rate Limiting**: As APIs públicas podem ter limites de requisições
- **Disponibilidade**: Dependente da disponibilidade das APIs externas
- **Dados**: Os dados retornados dependem do que cada API fornece

## Expansões Futuras

- [ ] Cache de respostas para reduzir chamadas às APIs
- [ ] Mais APIs de fallback
- [ ] Endpoint para consulta de CPF
- [ ] Endpoint para consulta de CEP
- [ ] Métricas de uso e disponibilidade das APIs
- [ ] Rate limiting interno
- [ ] Webhook para notificações de consultas

## Exemplo de Resposta Completa

```json
{
  "success": true,
  "cnpj": "27865757000102",
  "source": "https://open.cnpja.com/office/27865757000102",
  "data": {
    "taxId": "27865757000102",
    "updated": "2023-10-15T12:34:56.789Z",
    "company": {
      "id": 278657,
      "name": "MAGAZINE LUIZA S.A.",
      "equity": 1234567890.00,
      "nature": {
        "id": 2046,
        "text": "Sociedade Anônima Aberta"
      },
      "size": {
        "id": 5,
        "acronym": "DEMAIS",
        "text": "Demais"
      }
    },
    "alias": "MAGALU",
    "founded": "1957-11-16",
    "head": true,
    "statusDate": "2005-11-03",
    "status": {
      "id": 2,
      "text": "Ativa"
    },
    "address": {
      "municipality": 3543402,
      "street": "RUA VOLUNTÁRIOS DA FRANCA",
      "number": "1465",
      "district": "CENTRO",
      "city": "Franca",
      "state": "SP",
      "zip": "14400685"
    },
    "phones": [
      {
        "area": "16",
        "number": "37119500"
      }
    ],
    "emails": [
      {
        "address": "contato@magazineluiza.com.br"
      }
    ],
    "mainActivity": {
      "id": 4713002,
      "text": "Lojas de departamentos ou magazines"
    },
    "sideActivities": [
      {
        "id": 4789099,
        "text": "Comércio varejista de outros produtos não especificados anteriormente"
      }
    ]
  }
}
```

