# Gov Service - Endpoints de Tributação

## 📋 Visão Geral

O `gov-service` agora oferece endpoints mockup para consulta de informações tributárias, incluindo NCM e ICMS. Os dados são gerados de forma consistente e persistidos no Redis para garantir que consultas sucessivas retornem os mesmos valores.

## 🔧 Tecnologias

- **FastAPI**: Framework web
- **Redis**: Cache persistente para valores simulados
- **BrasilAPI**: Fonte real de descrições NCM
- **Requests**: Cliente HTTP

## 📡 Endpoints Disponíveis

### 1. Consulta NCM

**Endpoint:** `GET /ncm/consultar`

**Descrição:** Retorna informações tributárias de um código NCM, incluindo descrição real obtida da BrasilAPI.

**Parâmetros:**
- `ncm` (query, obrigatório): Código NCM com 8 dígitos
  - Formato: `^[0-9]{8}$`
  - Exemplo: `84713012`

**Exemplo de Requisição:**
```bash
curl "http://localhost:8003/ncm/consultar?ncm=84713012"
```

**Exemplo de Resposta:**
```json
{
  "ncm": "84713012",
  "descricao": "De peso inferior a 3,5 kg, com tela de área superior a 140 cm² mas inferior a 560 cm²",
  "tributacao_pis_cofins": {
    "regime_especial": "Monofasico",
    "aliquota_pis_padrao": 1.2,
    "aliquota_cofins_padrao": 5.5
  },
  "aliquota_ipi_padrao": 25.0
}
```

**Campos do Retorno:**
- `ncm`: Código NCM consultado
- `descricao`: Descrição do produto (obtida da BrasilAPI)
- `tributacao_pis_cofins`:
  - `regime_especial`: Regime tributário (Nenhum, Monofasico, Aliquota_Zero, Substituicao_Tributaria)
  - `aliquota_pis_padrao`: Alíquota de PIS (0.65% a 2.1%)
  - `aliquota_cofins_padrao`: Alíquota de COFINS (3.0% a 8.6%)
- `aliquota_ipi_padrao`: Alíquota de IPI (0%, 5%, 10%, 15%, 20%, 25%)

---

### 2. Consulta Alíquotas ICMS

**Endpoint:** `GET /icms/consultar_aliquotas`

**Descrição:** Retorna alíquotas e regras de ICMS para operações interestaduais, incluindo informações sobre Substituição Tributária (ST), DIFAL e FCP.

**Parâmetros:**
- `uf_origem` (query, obrigatório): UF de origem (sigla)
  - Formato: `^[A-Z]{2}$`
  - Exemplo: `SC`
- `uf_destino` (query, obrigatório): UF de destino (sigla)
  - Formato: `^[A-Z]{2}$`
  - Exemplo: `SP`
- `ncm` (query, obrigatório): Código NCM com 8 dígitos
  - Formato: `^[0-9]{8}$`
  - Exemplo: `84713012`
- `tipo_operacao` (query, opcional): Tipo de operação
  - Valores: `VENDA_PRODUTO`, `PRESTACAO_SERVICO`, `DEVOLUCAO`
  - Padrão: `VENDA_PRODUTO`
- `data_referencia` (query, opcional): Data de referência
  - Formato: `YYYY-MM-DD`
  - Exemplo: `2024-01-15`

**Exemplo de Requisição:**
```bash
curl "http://localhost:8003/icms/consultar_aliquotas?uf_origem=SC&uf_destino=SP&ncm=84713012"
```

**Exemplo de Resposta:**
```json
{
  "ncm": "84713012",
  "uf_origem": "SC",
  "uf_destino": "SP",
  "aliquota_interna_origem": 17.0,
  "aliquota_interna_destino": 18.0,
  "aliquota_interestadual": 12.0,
  "icms_st_aplicavel": false,
  "mva_original_icms_st": 0,
  "regime_icms_para_ncm": "TRIBUTADO_NORMAL",
  "aliquota_fcp_destino": 0,
  "aliquota_difal_origem": 17.0,
  "aliquota_difal_destino": 18.0,
  "partilha_difal_origem": 0,
  "partilha_difal_destino": 100
}
```

**Campos do Retorno:**
- `ncm`: Código NCM consultado
- `uf_origem`: UF de origem
- `uf_destino`: UF de destino
- `aliquota_interna_origem`: Alíquota interna da UF de origem
- `aliquota_interna_destino`: Alíquota interna da UF de destino
- `aliquota_interestadual`: Alíquota interestadual (geralmente 7% ou 12%)
- `icms_st_aplicavel`: Se é aplicável Substituição Tributária
- `mva_original_icms_st`: Margem de Valor Agregado para ST (20% a 50% se aplicável)
- `regime_icms_para_ncm`: Regime ICMS (TRIBUTADO_NORMAL, SUBSTITUICAO_TRIBUTARIA, ISENTO, REDUCAO_BASE_CALCULO)
- `aliquota_fcp_destino`: Alíquota do Fundo de Combate à Pobreza (0%, 1% ou 2%)
- `aliquota_difal_origem`: Alíquota para cálculo de DIFAL origem
- `aliquota_difal_destino`: Alíquota para cálculo de DIFAL destino
- `partilha_difal_origem`: Percentual de partilha do DIFAL para origem
- `partilha_difal_destino`: Percentual de partilha do DIFAL para destino

---

## 🔐 Persistência e Consistência

### Cache Redis

Todos os valores gerados são armazenados no Redis com TTL de 30 dias. Isso garante:

1. **Consistência**: Chamadas sucessivas com os mesmos parâmetros retornam valores idênticos
2. **Performance**: Respostas instantâneas após a primeira consulta
3. **Persistência**: Dados sobrevivem a reinicializações do serviço

### Geração de Valores

Os valores são gerados usando um **seed determinístico** baseado nos parâmetros de entrada:

- **NCM**: `MD5(ncm)` → seed
- **ICMS**: `MD5(uf_origem:uf_destino:ncm)` → seed

Isso garante que:
- Mesmos parâmetros = mesmos valores
- Valores são "razoáveis" (não muito altos nem muito baixos)
- Distribuição aleatória mas consistente

### Alíquotas Internas por UF

As alíquotas internas são baseadas em valores reais aproximados:

| UF  | Alíquota Interna |
|-----|------------------|
| AC  | 17.0%            |
| AL  | 18.0%            |
| BA  | 18.0%            |
| CE  | 18.0%            |
| DF  | 18.0%            |
| ES  | 17.0%            |
| GO  | 17.0%            |
| MA  | 18.0%            |
| MG  | 18.0%            |
| MS  | 17.0%            |
| MT  | 17.0%            |
| PA  | 17.0%            |
| PB  | 18.0%            |
| PE  | 18.0%            |
| PI  | 18.0%            |
| PR  | 18.0%            |
| RJ  | 20.0%            |
| RN  | 18.0%            |
| RO  | 17.5%            |
| RR  | 17.0%            |
| RS  | 18.0%            |
| SC  | 17.0%            |
| SE  | 18.0%            |
| SP  | 18.0%            |
| TO  | 18.0%            |

### Alíquotas Interestaduais

- **Região Sul/Sudeste → Região Sul/Sudeste**: 12%
- **Outras combinações**: 7%

### DIFAL (Diferencial de Alíquota)

A partir de 2023, a partilha do DIFAL é 100% para o estado de destino em operações para não contribuintes.

---

## 🧪 Exemplos de Uso

### Consultar NCM de Notebook
```bash
curl "http://localhost:8003/ncm/consultar?ncm=84713012"
```

### Consultar NCM de Gasolina
```bash
curl "http://localhost:8003/ncm/consultar?ncm=27101910"
```

### Consultar ICMS SC → SP
```bash
curl "http://localhost:8003/icms/consultar_aliquotas?uf_origem=SC&uf_destino=SP&ncm=84713012"
```

### Consultar ICMS BA → RJ
```bash
curl "http://localhost:8003/icms/consultar_aliquotas?uf_origem=BA&uf_destino=RJ&ncm=27101910"
```

### Consultar ICMS mesma UF (sem DIFAL)
```bash
curl "http://localhost:8003/icms/consultar_aliquotas?uf_origem=MG&uf_destino=MG&ncm=84714100"
```

---

## 🚀 Deploy

### Dependências

```
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
requests==2.31.0
redis==5.0.1
```

### Variáveis de Ambiente

```bash
SERVICE_PORT=8003
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

### Docker Compose

O serviço depende do Redis:

```yaml
gov-service:
  depends_on:
    redis:
      condition: service_healthy
```

---

## 🔍 Health Check

```bash
curl http://localhost:8003/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "gov_service",
  "redis": "connected"
}
```

---

## 🗑️ Limpeza de Cache

Para limpar todo o cache Redis:

```bash
docker exec redis redis-cli FLUSHALL
```

Para limpar apenas chaves específicas:

```bash
# Limpar todos os NCMs
docker exec redis redis-cli KEYS "ncm:*" | xargs docker exec redis redis-cli DEL

# Limpar todos os ICMS
docker exec redis redis-cli KEYS "icms:*" | xargs docker exec redis redis-cli DEL
```

---

## 📚 Integrações

### BrasilAPI

O endpoint `/ncm/consultar` utiliza a [BrasilAPI](https://brasilapi.com.br/) para obter descrições reais dos códigos NCM:

- **URL**: `https://brasilapi.com.br/api/ncm/v1/{code}`
- **Documentação**: https://brasilapi.com.br/docs#tag/NCM
- **Fallback**: Se a API falhar, retorna uma descrição genérica

---

## ⚠️ Observações

1. **Valores Simulados**: Este é um serviço mockup. Os valores tributários são simulados e não devem ser usados para cálculos fiscais reais.

2. **Descrições NCM**: As descrições são reais (obtidas da BrasilAPI), mas as alíquotas são simuladas.

3. **Cache Persistente**: Os valores ficam armazenados no Redis por 30 dias. Se precisar de novos valores, limpe o cache.

4. **Consistência**: Para as mesmas entradas, os valores gerados serão sempre os mesmos, mesmo após reinicializações.

5. **Alíquotas Reais vs Simuladas**: As alíquotas internas por UF são baseadas em valores reais aproximados, mas os outros valores (MVA, FCP, regimes) são gerados aleatoriamente com seed determinístico.

