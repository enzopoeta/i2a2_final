# Gov Service MCP Server

## 📋 Visão Geral

Servidor MCP (Model Context Protocol) que expõe as funcionalidades do `gov-service` através de uma interface HTTP padronizada. Permite que LLMs e outros agentes de IA consultem informações tributárias brasileiras.

## 🔧 O que é MCP?

O Model Context Protocol (MCP) é um protocolo padrão para integração de ferramentas e recursos com Large Language Models (LLMs). Ele define:

- **Tools**: Funções que o LLM pode chamar
- **Resources**: Dados que o LLM pode acessar
- **Prompts**: Templates de prompts reutilizáveis

## 🚀 Ferramentas Disponíveis

### 1. consultar_ncm

Consulta informações tributárias de um código NCM.

**Parâmetros:**
- `ncm` (string, obrigatório): Código NCM com 8 dígitos

**Retorna:**
- Descrição do produto (da BrasilAPI)
- Regime de PIS/COFINS
- Alíquotas de PIS, COFINS e IPI

**Exemplo:**
```json
{
  "name": "consultar_ncm",
  "arguments": {
    "ncm": "84713012"
  }
}
```

### 2. consultar_icms

Consulta alíquotas e regras de ICMS para operações interestaduais.

**Parâmetros:**
- `uf_origem` (string, obrigatório): UF de origem (ex: "SC")
- `uf_destino` (string, obrigatório): UF de destino (ex: "SP")
- `ncm` (string, obrigatório): Código NCM com 8 dígitos
- `tipo_operacao` (string, opcional): Tipo de operação (VENDA_PRODUTO, PRESTACAO_SERVICO, DEVOLUCAO)

**Retorna:**
- Alíquotas internas e interestaduais
- Informações sobre ST (Substituição Tributária)
- MVA (Margem de Valor Agregado)
- DIFAL (Diferencial de Alíquota)
- FCP (Fundo de Combate à Pobreza)

**Exemplo:**
```json
{
  "name": "consultar_icms",
  "arguments": {
    "uf_origem": "SC",
    "uf_destino": "SP",
    "ncm": "84713012"
  }
}
```

### 3. consultar_cnpj

Consulta informações cadastrais de um CNPJ.

**Parâmetros:**
- `cnpj` (string, obrigatório): CNPJ com 14 dígitos

**Retorna:**
- Razão social
- Nome fantasia
- Endereço completo
- Atividades econômicas
- Situação cadastral

**Exemplo:**
```json
{
  "name": "consultar_cnpj",
  "arguments": {
    "cnpj": "00000000000191"
  }
}
```

## 📡 API HTTP

### Endpoints

#### GET /health
Health check do servidor MCP.

**Resposta:**
```json
{
  "status": "healthy",
  "service": "gov-service-mcp",
  "transport": "http"
}
```

#### GET /tools
Lista todas as ferramentas disponíveis.

**Resposta:**
```json
{
  "tools": [
    {
      "name": "consultar_ncm",
      "description": "Consulta informações tributárias de um código NCM...",
      "inputSchema": { ... }
    },
    ...
  ]
}
```

#### POST /tools/call
Executa uma ferramenta.

**Request Body:**
```json
{
  "name": "consultar_ncm",
  "arguments": {
    "ncm": "84713012"
  }
}
```

**Resposta:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{ \"ncm\": \"84713012\", ... }"
    }
  ]
}
```

## 🐳 Docker

### Build
```bash
docker build -t gov-service-mcp ./services/gov_service_mcp
```

### Run
```bash
docker run -p 8005:8005 \
  -e GOV_SERVICE_URL=http://gov-service:8003 \
  -e TRANSPORT_MODE=http \
  -e MCP_PORT=8005 \
  gov-service-mcp
```

### Docker Compose
```yaml
gov-service-mcp:
  build:
    context: ./services/gov_service_mcp
  ports:
    - "8005:8005"
  environment:
    - TRANSPORT_MODE=http
    - MCP_PORT=8005
    - GOV_SERVICE_URL=http://gov-service:8003
  depends_on:
    - gov-service
  networks:
    - app-network
```

## 🧪 Exemplos de Uso

### cURL

#### Listar ferramentas
```bash
curl http://localhost:8005/tools
```

#### Consultar NCM
```bash
curl -X POST http://localhost:8005/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "consultar_ncm",
    "arguments": {
      "ncm": "84713012"
    }
  }'
```

#### Consultar ICMS
```bash
curl -X POST http://localhost:8005/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "consultar_icms",
    "arguments": {
      "uf_origem": "SC",
      "uf_destino": "SP",
      "ncm": "84713012"
    }
  }'
```

#### Consultar CNPJ
```bash
curl -X POST http://localhost:8005/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "consultar_cnpj",
    "arguments": {
      "cnpj": "00000000000191"
    }
  }'
```

### Python
```python
import requests

# Listar ferramentas
response = requests.get("http://localhost:8005/tools")
print(response.json())

# Consultar NCM
response = requests.post(
    "http://localhost:8005/tools/call",
    json={
        "name": "consultar_ncm",
        "arguments": {"ncm": "84713012"}
    }
)
print(response.json())
```

### JavaScript
```javascript
// Listar ferramentas
const tools = await fetch("http://localhost:8005/tools").then(r => r.json());
console.log(tools);

// Consultar NCM
const result = await fetch("http://localhost:8005/tools/call", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "consultar_ncm",
    arguments: { ncm: "84713012" }
  })
}).then(r => r.json());
console.log(result);
```

## 🔗 Integração com Claude Desktop

Para usar com Claude Desktop, adicione ao seu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gov-service": {
      "command": "node",
      "args": ["/caminho/para/gov_service_mcp/index.js"],
      "env": {
        "GOV_SERVICE_URL": "http://localhost:8003",
        "TRANSPORT_MODE": "stdio"
      }
    }
  }
}
```

Ou via HTTP com um proxy MCP:

```json
{
  "mcpServers": {
    "gov-service": {
      "url": "http://localhost:8005"
    }
  }
}
```

## 🌐 Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `TRANSPORT_MODE` | Modo de transporte (stdio ou http) | `stdio` |
| `MCP_PORT` | Porta do servidor HTTP | `8005` |
| `GOV_SERVICE_URL` | URL do gov-service | `http://gov-service:8003` |

## 📚 Referências

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP SDK](https://github.com/modelcontextprotocol/sdk)
- [Gov Service README](../gov_service/README_TRIBUTACAO.md)

## ⚠️ Observações

1. **Modo HTTP**: Por padrão, o MCP usa STDIO para comunicação. Este servidor adiciona suporte HTTP para facilitar integrações web.

2. **Valores Simulados**: Os dados tributários são simulados. Não use para cálculos fiscais reais.

3. **Cache**: Os valores são cacheados no Redis por 30 dias para consistência.

4. **Rate Limiting**: Não há rate limiting implementado. Adicione se necessário para ambientes de produção.

