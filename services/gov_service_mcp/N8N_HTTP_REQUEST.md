# Como usar Gov Service no n8n via HTTP Request

## ❗ IMPORTANTE

O nó **MCP Client** do n8n **NÃO suporta HTTP**! Ele só funciona com servidores MCP em modo STDIO (linha de comando local).

Para usar nosso gov-service-mcp no n8n, use o nó **HTTP Request** padrão.

## 🔧 Configuração no n8n

### Método 1: Endpoints REST Diretos

Use os endpoints REST customizados:

#### Consultar NCM

**Nó:** HTTP Request
- **Method:** POST
- **URL:** `http://gov-service-mcp:8005/tools/call`
- **Body Content Type:** JSON
- **Body:**
```json
{
  "name": "consultar_ncm",
  "arguments": {
    "ncm": "84713012"
  }
}
```

#### Consultar ICMS

**Nó:** HTTP Request
- **Method:** POST
- **URL:** `http://gov-service-mcp:8005/tools/call`
- **Body:**
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

#### Consultar CNPJ

**Nó:** HTTP Request
- **Method:** POST
- **URL:** `http://gov-service-mcp:8005/tools/call`
- **Body:**
```json
{
  "name": "consultar_cnpj",
  "arguments": {
    "cnpj": "00000000000191"
  }
}
```

### Método 2: Endpoints Gov-Service Diretos

Use diretamente o gov-service (sem MCP):

#### Consultar NCM

**Nó:** HTTP Request
- **Method:** GET
- **URL:** `http://gov-service:8003/ncm/consultar?ncm=84713012`

#### Consultar ICMS

**Nó:** HTTP Request
- **Method:** GET  
- **URL:** `http://gov-service:8003/icms/consultar_aliquotas?uf_origem=SC&uf_destino=SP&ncm=84713012`

#### Consultar CNPJ

**Nó:** HTTP Request
- **Method:** GET
- **URL:** `http://gov-service:8003/cnpjinfo/00000000000191`

## 📊 Workflow Completo Exemplo

```
┌─────────────────┐
│  Webhook NF     │ Recebe dados da NF
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Loop Itens     │ Para cada item
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │ Consultar NCM
│  (Gov Service)  │ GET /ncm/consultar?ncm={{$json.ncm}}
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │ Consultar ICMS
│  (Gov Service)  │ GET /icms/consultar_aliquotas?...
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Code Node      │ Calcular impostos
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save to DB     │
└─────────────────┘
```

## 🎯 Exemplo Completo: Calcular Impostos de Item

### Passo 1: HTTP Request - Consultar NCM

**Configuração:**
- URL: `http://gov-service:8003/ncm/consultar`
- Query Parameters:
  - `ncm`: `{{ $json.ncm }}`

**Resposta:**
```json
{
  "ncm": "84713012",
  "descricao": "De peso inferior a 3,5 kg...",
  "tributacao_pis_cofins": {
    "regime_especial": "Monofasico",
    "aliquota_pis_padrao": 1.2,
    "aliquota_cofins_padrao": 5.5
  },
  "aliquota_ipi_padrao": 25
}
```

### Passo 2: HTTP Request - Consultar ICMS

**Configuração:**
- URL: `http://gov-service:8003/icms/consultar_aliquotas`
- Query Parameters:
  - `uf_origem`: `{{ $json.uf_origem }}`
  - `uf_destino`: `{{ $json.uf_destino }}`
  - `ncm`: `{{ $json.ncm }}`

### Passo 3: Code Node - Calcular Impostos

```javascript
// Pegar dados dos nodes anteriores
const ncmData = $('Consultar NCM').first().json;
const icmsData = $('Consultar ICMS').first().json;
const item = $input.first().json;

const valorBase = parseFloat(item.valor);

// Calcular PIS/COFINS
let valorPis = 0;
let valorCofins = 0;

if (ncmData.tributacao_pis_cofins.regime_especial === "Nenhum") {
  valorPis = valorBase * (ncmData.tributacao_pis_cofins.aliquota_pis_padrao / 100);
  valorCofins = valorBase * (ncmData.tributacao_pis_cofins.aliquota_cofins_padrao / 100);
}

// Calcular IPI
const valorIpi = valorBase * (ncmData.aliquota_ipi_padrao / 100);

// Calcular ICMS
const valorIcms = valorBase * (icmsData.aliquota_interestadual / 100);

// Calcular DIFAL
let valorDifal = 0;
if (icmsData.uf_origem !== icmsData.uf_destino) {
  const difal = icmsData.aliquota_difal_destino - icmsData.aliquota_interestadual;
  valorDifal = valorBase * (difal / 100);
}

const totalTributos = valorPis + valorCofins + valorIpi + valorIcms + valorDifal;

return {
  json: {
    ...item,
    ncm_descricao: ncmData.descricao,
    impostos: {
      pis: valorPis,
      cofins: valorCofins,
      ipi: valorIpi,
      icms: valorIcms,
      difal: valorDifal,
      total: totalTributos
    },
    carga_tributaria: (totalTributos / valorBase) * 100
  }
};
```

## 🔗 Usando Expressões do n8n

Para acessar dados dos requests anteriores:

### Via MCP (tool/call):
```javascript
// Extrair dados do MCP response
{{ JSON.parse($json.content[0].text).ncm }}
{{ JSON.parse($json.content[0].text).descricao }}
```

### Via Gov-Service direto:
```javascript
// Dados já vêm no formato correto
{{ $json.ncm }}
{{ $json.descricao }}
```

## 💡 Dica: Qual usar?

### Use Gov-Service Direto quando:
- ✅ Workflow simples
- ✅ Quer performance máxima
- ✅ Prefere GET requests

### Use MCP (via HTTP Request) quando:
- ✅ Quer manter compatibilidade com protocolo MCP
- ✅ Pode usar o mesmo formato em outros sistemas
- ✅ Prefere POST requests

## 🐛 Troubleshooting

### Erro: "Cannot resolve host"
- **Causa:** n8n não consegue resolver `gov-service-mcp`
- **Solução:** Certifique-se que ambos estão na mesma rede Docker

### Resposta vazia
- **Causa:** Parâmetros incorretos
- **Solução:** Verifique os query parameters ou JSON body

### Timeout
- **Causa:** Gov service está offline
- **Solução:** Verifique `docker ps | grep gov-service`

## 📚 Referências

- [Gov Service REST API](./README_TRIBUTACAO.md)
- [Gov Service MCP](./README.md)
- [n8n HTTP Request Node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)

