# Como usar o Gov Service MCP no n8n

## 📋 Visão Geral

O n8n tem suporte nativo para servidores MCP via o nó **"MCP Client"**. Este guia mostra como integrar o `gov-service-mcp` com o n8n para consultas tributárias em workflows.

## 🔧 Configuração no n8n

### Passo 1: Adicionar o nó MCP Client

1. Abra seu workflow no n8n
2. Adicione um novo nó
3. Procure por **"MCP Client"**
4. Clique para adicionar ao workflow

### Passo 2: Configurar a Conexão

No nó MCP Client, configure os seguintes parâmetros:

| Campo | Valor | Descrição |
|-------|-------|-----------|
| **Endpoint** | `http://gov-service-mcp:8005` | URL interna do Docker |
| **Server Transport** | `HTTP Streamable` | Tipo de transporte |
| **Authentication** | `None` | Sem autenticação |
| **Tools to Include** | `All` | Todas as ferramentas disponíveis |

#### Se acessar de fora do Docker:
- **Endpoint**: `http://localhost:8005`

### Passo 3: Configurar a Ferramenta

Após conectar, você verá 3 ferramentas disponíveis:

1. **consultar_ncm**
2. **consultar_icms**
3. **consultar_cnpj**

## 🎯 Exemplos de Uso

### Exemplo 1: Consultar NCM de um Produto

**Workflow:**
```
Trigger (Webhook/Manual) → MCP Client → Process Result
```

**Configuração do MCP Client:**
- **Tool**: `consultar_ncm`
- **Parameters**:
  ```json
  {
    "ncm": "84713012"
  }
  ```

**Resposta esperada:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"ncm\": \"84713012\",\n  \"descricao\": \"De peso inferior a 3,5 kg...\",\n  \"tributacao_pis_cofins\": {...},\n  \"aliquota_ipi_padrao\": 25\n}"
    }
  ]
}
```

**Para extrair os dados:**
- Use uma expressão: `{{ JSON.parse($json.content[0].text) }}`

### Exemplo 2: Calcular ICMS Interestadual

**Workflow:**
```
Webhook (recebe dados da NF) → MCP Client → Calculate Taxes → Save to DB
```

**Configuração do MCP Client:**
- **Tool**: `consultar_icms`
- **Parameters**:
  ```json
  {
    "uf_origem": "SC",
    "uf_destino": "SP",
    "ncm": "84713012"
  }
  ```

**Processamento dos dados:**
```javascript
// Code node para processar a resposta
const mcpResponse = JSON.parse($input.first().json.content[0].text);

const difal = mcpResponse.aliquota_difal_destino - mcpResponse.aliquota_interestadual;
const valorDifal = valorProduto * (difal / 100);

return {
  json: {
    ncm: mcpResponse.ncm,
    aliquota_interestadual: mcpResponse.aliquota_interestadual,
    aliquota_destino: mcpResponse.aliquota_difal_destino,
    diferencial: difal,
    valor_difal: valorDifal,
    st_aplicavel: mcpResponse.icms_st_aplicavel,
    mva: mcpResponse.mva_original_icms_st
  }
};
```

### Exemplo 3: Enriquecer Nota Fiscal com Dados Tributários

**Workflow complexo:**
```
Trigger (Nova NF) → Loop (Itens) → MCP Client (NCM) → MCP Client (ICMS) → Aggregate → Save
```

**Nó 1 - Loop nos Itens:**
```javascript
// Split Into Items node
return $input.items.map(item => ({
  json: {
    item_id: item.json.id,
    ncm: item.json.ncm,
    valor: item.json.valor,
    uf_origem: item.json.uf_origem,
    uf_destino: item.json.uf_destino
  }
}));
```

**Nó 2 - Consultar NCM:**
- **Tool**: `consultar_ncm`
- **Parameters**: `{ "ncm": "{{ $json.ncm }}" }`

**Nó 3 - Consultar ICMS:**
- **Tool**: `consultar_icms`
- **Parameters**: 
  ```json
  {
    "uf_origem": "{{ $json.uf_origem }}",
    "uf_destino": "{{ $json.uf_destino }}",
    "ncm": "{{ $json.ncm }}"
  }
  ```

**Nó 4 - Merge e Calcular:**
```javascript
// Code node
const ncmData = JSON.parse($('MCP_NCM').first().json.content[0].text);
const icmsData = JSON.parse($('MCP_ICMS').first().json.content[0].text);
const item = $('Loop').first().json;

// Calcular PIS/COFINS
const valorPis = item.valor * (ncmData.tributacao_pis_cofins.aliquota_pis_padrao / 100);
const valorCofins = item.valor * (ncmData.tributacao_pis_cofins.aliquota_cofins_padrao / 100);

// Calcular IPI
const valorIpi = item.valor * (ncmData.aliquota_ipi_padrao / 100);

// Calcular ICMS
const valorIcms = item.valor * (icmsData.aliquota_interestadual / 100);

// Calcular DIFAL se aplicável
let valorDifal = 0;
if (icmsData.aliquota_difal_destino > 0) {
  const difal = icmsData.aliquota_difal_destino - icmsData.aliquota_interestadual;
  valorDifal = item.valor * (difal / 100);
}

return {
  json: {
    item_id: item.item_id,
    ncm: item.ncm,
    descricao_ncm: ncmData.descricao,
    valor_base: item.valor,
    tributos: {
      pis: {
        aliquota: ncmData.tributacao_pis_cofins.aliquota_pis_padrao,
        valor: valorPis,
        regime: ncmData.tributacao_pis_cofins.regime_especial
      },
      cofins: {
        aliquota: ncmData.tributacao_pis_cofins.aliquota_cofins_padrao,
        valor: valorCofins
      },
      ipi: {
        aliquota: ncmData.aliquota_ipi_padrao,
        valor: valorIpi
      },
      icms: {
        aliquota_interestadual: icmsData.aliquota_interestadual,
        valor_icms: valorIcms,
        aliquota_destino: icmsData.aliquota_interna_destino,
        st_aplicavel: icmsData.icms_st_aplicavel,
        mva: icmsData.mva_original_icms_st
      },
      difal: {
        aplicavel: valorDifal > 0,
        valor: valorDifal,
        partilha_origem: icmsData.partilha_difal_origem,
        partilha_destino: icmsData.partilha_difal_destino
      }
    },
    valor_total_tributos: valorPis + valorCofins + valorIpi + valorIcms + valorDifal
  }
};
```

## 📊 Workflow Completo: Processamento de Nota Fiscal

```
┌─────────────────┐
│  Webhook NF     │ Recebe XML da NF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parse XML      │ Extrai dados da NF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Loop Itens     │ Itera sobre cada item
└────────┬────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│  MCP: NCM       │       │  MCP: ICMS      │
└────────┬────────┘       └────────┬────────┘
         │                         │
         └─────────┬───────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Calc Tributos  │ Calcula impostos
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Aggregate      │ Agrupa resultados
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Save to DB     │ Salva no PostgreSQL
         └─────────────────┘
```

## 🔗 Integração com Sistema Existente

### Criar Workflow de Cálculo de Impostos

1. **Trigger**: HTTP Webhook em `/webhook/calcular-impostos-nf`
2. **Input**: JSON com dados da nota fiscal
3. **Process**: 
   - Extrai itens da NF
   - Consulta NCM para cada item
   - Consulta ICMS para operação
   - Calcula todos os impostos
4. **Output**: JSON com tributos calculados

### Conectar com o taxes_service

No `taxes_service`, já existe um webhook que envia para n8n:

**taxes_service/main.py:**
```python
# Linha ~75
webhook_response = requests.post(
    TAXES_WEBHOOK_URL,  # http://n8n:5678/webhook/taxes-nf
    json=nota_fiscal_data,
    headers={'Content-Type': 'application/json'},
    timeout=30
)
```

**Criar workflow no n8n para processar isso:**

1. **Webhook Node**: `/webhook/taxes-nf`
2. **MCP Client - Loop**: Para cada item da NF
   - Consulta NCM
   - Consulta ICMS
3. **Function Node**: Calcula impostos
4. **HTTP Request**: Retorna resultado ou salva no DB

## 🎨 Template de Workflow (JSON)

```json
{
  "name": "Calcular Impostos - Gov Service MCP",
  "nodes": [
    {
      "parameters": {
        "path": "calcular-impostos",
        "method": "POST"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "endpoint": "http://gov-service-mcp:8005",
        "serverTransport": "HTTP Streamable",
        "authentication": "none",
        "toolsToInclude": "all"
      },
      "name": "MCP Client - NCM",
      "type": "@n8n/n8n-nodes-mcp.mcpClient",
      "position": [450, 300]
    },
    {
      "parameters": {
        "endpoint": "http://gov-service-mcp:8005",
        "serverTransport": "HTTP Streamable",
        "authentication": "none",
        "toolsToInclude": "all"
      },
      "name": "MCP Client - ICMS",
      "type": "@n8n/n8n-nodes-mcp.mcpClient",
      "position": [450, 450]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "MCP Client - NCM",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "MCP Client - NCM": {
      "main": [
        [
          {
            "node": "MCP Client - ICMS",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## 🐛 Troubleshooting

### Erro: "Cannot connect to MCP server"

**Causa**: n8n não consegue acessar o endpoint.

**Solução**:
1. Verifique se o container está rodando:
   ```bash
   docker ps | grep mcp
   ```

2. Teste o endpoint manualmente:
   ```bash
   curl http://localhost:8005/health
   ```

3. Se n8n está em outro container, use o nome do serviço:
   ```
   http://gov-service-mcp:8005
   ```

### Erro: "Tool not found"

**Causa**: Nome da ferramenta incorreto.

**Solução**: Use os nomes exatos:
- `consultar_ncm`
- `consultar_icms`
- `consultar_cnpj`

### Dados não aparecem

**Causa**: Response está em formato texto JSON dentro de `content[0].text`.

**Solução**: Use expressão para extrair:
```javascript
{{ JSON.parse($json.content[0].text) }}
```

## 📚 Recursos Adicionais

- [Documentação n8n MCP Client](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.mcpclient/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Gov Service MCP README](./README.md)

## 💡 Dicas

1. **Cache**: O Redis já está configurado, então consultas repetidas são instantâneas
2. **Batch Processing**: Use o node "Split In Batches" para processar muitos itens
3. **Error Handling**: Adicione nodes de "If" para tratar erros do MCP
4. **Logging**: Use "Set" node para logar dados intermediários
5. **Performance**: Consultas paralelas podem ser feitas com "Merge" node

## 🔐 Segurança

Para produção, considere:

1. **Autenticação**: Adicionar API key no MCP server
2. **Rate Limiting**: Limitar requests por IP
3. **HTTPS**: Usar certificados SSL/TLS
4. **Network**: Isolar em rede privada do Docker

