# Sistema de Gestão e Análise de Notas Fiscais Eletrônicas

Sistema completo para processamento, armazenamento, análise e consulta inteligente de Notas Fiscais Eletrônicas (NF-e) utilizando arquitetura de microserviços, filas de mensagens, agentes de IA e integração com APIs governamentais.

---

## 🎥 Vídeo Demonstrativo

Assista ao vídeo de demonstração do sistema em ação:

[![Demonstração do Sistema](https://img.youtube.com/vi/14hAdeokT3g/maxresdefault.jpg)](https://youtu.be/14hAdeokT3g)

**🔗 Link direto**: [https://youtu.be/14hAdeokT3g](https://youtu.be/14hAdeokT3g)

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Serviços](#serviços)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Como Executar](#como-executar)
- [Utilização](#utilização)
- [APIs e Endpoints](#apis-e-endpoints)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Escalabilidade](#escalabilidade)
- [Segurança e Privacidade](#segurança-e-privacidade)

---

## 🎯 Visão Geral

Este sistema foi desenvolvido para empresas que precisam gerenciar grandes volumes de notas fiscais eletrônicas. Ele oferece:

- **Upload e parsing** automático de arquivos XML de NF-e
- **Armazenamento estruturado** em banco de dados PostgreSQL
- **Classificação inteligente** usando workflows no n8n
- **Análise fiscal completa** com integração a APIs governamentais e validações
- **Agentes de IA** para análise, consultas e geração de relatórios
- **Interface web moderna** para interação e visualização
- **Proteção de dados sensíveis** com anonimização automática

---

## 🏗️ Arquitetura

O sistema é composto por **8 microserviços** principais rodando em containers Docker:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CAMADA DE INTERFACE                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                     UI Service (Vue.js)                      │  │
│  │        Interface Web - Upload, Chat, Dashboards            │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐       ┌─────────▼─────────┐    ┌────────▼────────┐
│ Load Service  │       │   NF Agent        │    │  Site Service   │
│ (Upload/Parse)│       │ (AI Multi-Agent)  │    │ (Queries/Stats) │
└───────┬───────┘       └───────────────────┘    └────────┬────────┘
        │                                                   │
        │              ┌──────────────────┐                │
        └──────────────►   RabbitMQ       ◄────────────────┘
                       │  Message Broker  │
                       └────────┬─────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────────┐  ┌─────────▼────────┐  ┌─────────▼─────────┐
│ Onboarding       │  │ Taxes Service    │  │  Gov Service      │
│ Service          │  │ (Fiscal Analysis)│  │  (CNPJ Lookup)    │
└──────────────────┘  └──────────────────┘  └───────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │                       │
                    │   PostgreSQL          │
                    │   (Banco de Dados)    │
                    │                       │
                    └───────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    SERVIÇOS DE INFRAESTRUTURA                    │
│  ┌───────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │PostgreSQL │  │ RabbitMQ │  │   Redis     │  │    n8n     │ │
│  │           │  │          │  │   (Cache)   │  │ (Workflow) │ │
│  └───────────┘  └──────────┘  └─────────────┘  └────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

1. **Upload** → UI envia XML para Load Service
2. **Parsing** → Load Service extrai dados e salva no PostgreSQL
3. **Classificação** → Nota é enviada via RabbitMQ para Onboarding Service
4. **Workflow n8n** → Classifica a nota usando IA
5. **Análise Fiscal** → Taxes Service busca nota e realiza análise fiscal completa via Gov Service
6. **Análise Inteligente** → NF Agent permite consultas e análises usando agentes de IA
7. **Visualização** → UI exibe dados, status e permite interação

---

## ✨ Funcionalidades Principais

### 📤 Upload e Processamento
- Upload de arquivos XML individuais ou em lote (ZIP)
- Parser automático de NF-e (modelo 55)
- Validação e extração de dados estruturados
- Drag & drop com feedback visual em tempo real

### 🤖 Classificação Inteligente
- Classificação automática usando n8n + IA
- Categorização por tipo de produto/serviço
- Integração com webhooks para workflows externos

### 💰 Análise Fiscal
- Análise completa de tributos (ICMS, IPI, PIS, COFINS)
- Validação de alíquotas e bases de cálculo
- Verificação de conformidade fiscal
- Integração com APIs governamentais para dados atualizados
- Cache de resultados para performance

### 🔍 Consultas Governamentais
- Consulta de CNPJ em APIs públicas
- Fallback automático entre múltiplas APIs
- Validação e enriquecimento de dados

### 🧠 Agentes de IA (NF Agent)
Sistema multi-agente especializado para:
- **Análise de dados fiscais** com consultas SQL inteligentes
- **Geração de relatórios** personalizados
- **Sumarização** de informações complexas
- **Anonimização** automática de dados sensíveis
- **Gerenciamento de arquivos** para exportação
- **Interação conversacional** em tempo real

### 🎨 Interface Web Moderna
- Dashboard com métricas em tempo real
- Chat interativo com agente de IA
- Upload com drag & drop
- Visualizações e gráficos
- Design responsivo (desktop, tablet, mobile)

---

## 🔧 Serviços

### 1. **Load Service** (Porta 8000)
**Função**: Upload e parsing de NF-e

**Responsabilidades**:
- Recebe arquivos XML/ZIP via API
- Extrai dados da nota fiscal e itens
- Valida estrutura XML
- Persiste no PostgreSQL
- Publica evento no RabbitMQ para classificação

**Endpoints**:
- `POST /upload/` - Upload de arquivos
- `GET /health` - Health check
- `GET /status` - Status do banco de dados

---

### 2. **Onboarding Service** (Porta 8010)
**Função**: Classificação de notas fiscais

**Responsabilidades**:
- Consome fila RabbitMQ `notas_fiscais`
- Envia para webhook do n8n para classificação
- Atualiza classificação no banco de dados
- Suporta retry e Dead Letter Queue (DLQ)

**Endpoints**:
- `GET /health` - Health check
- `GET /status` - Status do serviço

---

### 3. **Taxes Service** (Porta 8002)
**Função**: Análise fiscal de notas

**Responsabilidades**:
- Busca nota fiscal completa do banco
- Realiza análise detalhada de tributos (ICMS, IPI, PIS, COFINS)
- Valida alíquotas aplicadas e bases de cálculo
- Verifica conformidade com legislação fiscal
- Integra com Gov Service para enriquecimento de dados
- Identifica possíveis inconsistências fiscais
- Atualiza análises e validações no banco

**Endpoints**:
- `POST /calculate-taxes/` - Analisar tributos de uma NF
- `GET /health` - Health check
- `GET /status` - Status e estatísticas

---

### 4. **Gov Service** (Porta 8003)
**Função**: Consultas governamentais

**Responsabilidades**:
- Consulta CNPJ em APIs públicas
- Fallback automático entre múltiplas APIs
- Cache de respostas no Redis
- Validação de dados

**Endpoints**:
- `GET /cnpjinfo/{cnpj}` - Consultar CNPJ
- `GET /health` - Health check
- `GET /status` - Status das APIs

**APIs Utilizadas**:
- https://open.cnpja.com
- https://publica.cnpj.ws

---

### 5. **Gov Service MCP** (Porta 8005)
**Função**: Wrapper MCP para Gov Service

**Responsabilidades**:
- Expõe Gov Service via protocolo MCP
- Integração com n8n via MCP
- Suporte a function calling

---

### 6. **Site Service** (Porta 8004)
**Função**: Queries e estatísticas

**Responsabilidades**:
- Consultas otimizadas ao banco de dados
- Estatísticas e agregações
- Filtros avançados
- Paginação

**Endpoints**:
- `GET /notas` - Listar notas fiscais
- `GET /notas/{id}` - Detalhes de uma nota
- `GET /stats` - Estatísticas gerais

---

### 7. **NF Agent** (Porta 8001)
**Função**: Sistema multi-agente inteligente

**Agentes Disponíveis**:
- **main_agent**: Coordenador geral
- **file_manager**: Manipulação de arquivos
- **pg_agent**: Consultas ao banco PostgreSQL
- **anon_agent**: Anonimização de dados
- **summarize_agent**: Sumarização de textos
- **user_proxy**: Interface com usuário

**Responsabilidades**:
- Coordena múltiplos agentes especializados
- Executa tarefas complexas colaborativamente
- Streaming de respostas em tempo real
- Garante anonimização de dados sensíveis

**Endpoints**:
- `POST /tasks/` - Criar nova tarefa
- `GET /tasks/` - Listar tarefas
- `POST /tasks/{id}/stream` - Stream de execução
- `POST /tasks/{id}/input` - Fornecer input

**Tecnologias**:
- AutoGen framework
- Ollama (LLM local)
- MCP (Model Context Protocol)
- Docker-in-Docker para agentes isolados

---

### 8. **UI Service** (Porta 8080)
**Função**: Interface web

**Responsabilidades**:
- Interface gráfica para todas as funcionalidades
- Upload de arquivos
- Chat com NF Agent
- Dashboard e visualizações
- Proxy reverso para serviços backend

**Tecnologias**:
- Vue.js 3 (Composition API)
- Vuetify 3 (Material Design)
- Pinia (State Management)
- Vite (Build Tool)
- Nginx (Web Server)

---

## 📦 Pré-requisitos

### Obrigatórios

1. **Docker** (versão 20.10+)
   ```bash
   docker --version
   ```

2. **Docker Compose** (versão 2.0+)
   ```bash
   docker compose version
   ```

### Recomendados

3. **Servidor Ollama** (para NF Agent)
   - Host: Configurável via `OLLAMA_HOST`
   - Modelos recomendados: `gpt-oss:20b`, `qwen2.5:32b-instruct-q8_0`

4. **Recursos Mínimos**
   - CPU: 4 cores
   - RAM: 8GB
   - Disco: 20GB livres

---

## 🚀 Instalação e Configuração

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd i2a2_final
```

### 2. Configuração de Variáveis de Ambiente

O sistema usa variáveis de ambiente definidas no `docker-compose.yml`. As principais são:

#### PostgreSQL
```yaml
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
DB_NAME=notasfiscais
```

#### RabbitMQ
```yaml
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=admin
```

#### Ollama (NF Agent)
```yaml
OLLAMA_HOST=192.168.0.120:11434
OLLAMA_MODEL=gpt-oss:20b
```

**⚠️ Importante**: Ajuste o `OLLAMA_HOST` para o endereço do seu servidor Ollama.

### 3. Estrutura de Diretórios

O sistema criará automaticamente os volumes necessários:

```
data/
├── n8n_data/          # Workflows e configurações do n8n
└── volumes/
    ├── postgres_data/  # Dados do PostgreSQL
    ├── rabbitmq_data/  # Filas do RabbitMQ
    ├── redis_data/     # Cache do Redis
    └── uploads_data/   # Arquivos enviados
```

---

## 🎬 Como Executar

### Iniciar Todos os Serviços

```bash
# Build e start de todos os serviços
docker compose up -d

# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f ui
```

### Iniciar Serviços Individualmente

```bash
# Apenas Load Service e dependências
docker compose up -d db rabbitmq loader-service

# Apenas NF Agent
docker compose up -d nf_agent

# Apenas UI
docker compose up -d ui
```

### Verificar Status

```bash
# Listar containers rodando
docker compose ps

# Status de saúde
docker compose ps --format json | jq '.[] | {name: .Name, status: .Status}'
```

### Rebuild de Serviços

Quando houver mudanças no código, faça rebuild forçado:

```bash
# Rebuild sem cache de um serviço específico
docker compose build --no-cache ui
docker compose up -d ui

# Rebuild de todos os serviços
docker compose build --no-cache
docker compose up -d
```

### Parar Serviços

```bash
# Parar todos
docker compose down

# Parar e remover volumes (apaga dados!)
docker compose down -v

# Parar um serviço específico
docker compose stop ui
```

---

## 📱 Utilização

### 1. Acessar a Interface Web

Abra seu navegador em: **http://localhost:8080**

### 2. Upload de Notas Fiscais

**Passo a passo**:

1. Acesse a página inicial
2. Clique na área de upload ou arraste arquivos
3. Selecione arquivos `.xml` ou `.zip` (máx. 100MB)
4. Aguarde o processamento
5. Verifique o status no dashboard

**Formatos aceitos**:
- Arquivos XML individuais de NF-e
- Arquivos ZIP contendo múltiplos XMLs

**Exemplo via API**:
```bash
curl -X POST http://localhost:8000/upload/ \
  -F "file=@nota_fiscal.xml"
```

### 3. Chat com o Agente de IA

Após o upload, o chat será habilitado automaticamente.

**Exemplos de comandos**:

```
"Analise as notas fiscais do mês de janeiro"
```

```
"Quais são os 10 produtos mais vendidos?"
```

```
"Gere um relatório de vendas por estado, com dados anonimizados"
```

```
"Analise a carga tributária das notas fiscais deste mês"
```

```
"Liste os emitentes com maior volume de notas"
```

### 4. Consultar Dados

**Via Interface Web**:
- Navegue até "Minhas Notas"
- Use filtros e busca
- Visualize detalhes de cada nota

**Via API direta**:
```bash
# Status do banco
curl http://localhost:8000/status

# Consultar CNPJ
curl http://localhost:8003/cnpjinfo/27865757000102

# Analisar tributos de uma nota
curl -X POST http://localhost:8002/calculate-taxes/ \
  -H "Content-Type: application/json" \
  -d '{"chave_acesso": "35250612345678000199550010000123451234567890"}'
```

---

## 🔌 APIs e Endpoints

### Load Service (`:8000`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/status` | Status do banco |
| POST | `/upload/` | Upload de NF-e |

### Onboarding Service (`:8010`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/status` | Status do serviço |

### Taxes Service (`:8002`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/status` | Status e estatísticas |
| POST | `/calculate-taxes/` | Analisar tributos da NF |

### Gov Service (`:8003`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/status` | Status das APIs |
| GET | `/cnpjinfo/{cnpj}` | Consultar CNPJ |

### Site Service (`:8004`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/notas` | Listar notas |
| GET | `/notas/{id}` | Detalhes da nota |
| GET | `/stats` | Estatísticas |

### NF Agent (`:8001`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Info do serviço |
| POST | `/tasks/` | Criar tarefa |
| GET | `/tasks/` | Listar tarefas |
| GET | `/tasks/{id}` | Status da tarefa |
| POST | `/tasks/{id}/stream` | Stream de execução |
| POST | `/tasks/{id}/input` | Fornecer input |
| DELETE | `/tasks/{id}` | Excluir tarefa |

### n8n (`:5678`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Interface web n8n |
| POST | `/webhook/nf-input` | Webhook classificação |
| POST | `/webhook/taxes-nf` | Webhook impostos |

### UI (`:8080`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Interface web |
| Proxy | `/api/load/*` | Load Service |
| Proxy | `/api/agent/*` | NF Agent |

---

## 🛠️ Tecnologias Utilizadas

### Backend

- **Python 3.11**
  - FastAPI (APIs REST)
  - AsyncPG (PostgreSQL async)
  - Pika (RabbitMQ client)
  - AutoGen (Multi-agent framework)

### Frontend

- **Vue.js 3** (Composition API)
- **Vuetify 3** (Material Design)
- **Pinia** (State Management)
- **Vite** (Build Tool)
- **Axios** (HTTP Client)

### Infraestrutura

- **PostgreSQL 15** (Banco de dados)
- **RabbitMQ 3.13** (Message Broker)
- **Redis 7** (Cache)
- **n8n** (Workflow Automation)
- **Nginx** (Web Server / Reverse Proxy)
- **Docker** (Containerização)

### IA e Machine Learning

- **Ollama** (LLM local)
- **AutoGen** (Multi-agent orchestration)
- **MCP** (Model Context Protocol)

---

## 📈 Escalabilidade

O sistema foi projetado para escalar horizontalmente.

### Escalar Serviços

```bash
# Escalar Taxes Service (análise fiscal) para 5 instâncias
docker compose up -d --scale taxes-service=5

# Escalar Onboarding Service para 3 instâncias
docker compose up -d --scale onboarding-service=3
```

### Características

✅ **Load Balancing Automático**: RabbitMQ distribui mensagens entre workers  
✅ **Sem Duplicação**: Cada mensagem é processada apenas uma vez  
✅ **Tolerância a Falhas**: Se um worker cai, outros assumem  
✅ **Distribuição Round-robin**: Balanceamento uniforme de carga

### Arquitetura Escalável

```
                  ┌──────────────┐
                  │  RabbitMQ    │
                  │    Queue     │
                  └──────┬───────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │Worker 1│      │Worker 2│      │Worker N│
    │(Inst 1)│      │(Inst 2)│      │(Inst N)│
    └────────┘      └────────┘      └────────┘
```

📖 **Mais detalhes**: Veja `services/*/ESCALABILIDADE.md`

---

## 🔒 Segurança e Privacidade

### Anonimização Automática

O sistema **NUNCA** retorna dados sensíveis sem anonimização.

**Dados Protegidos**:
- Nomes de pessoas
- Endereços
- Telefones
- E-mails
- CPF/CNPJ (quando configurado)

**Processo**:
1. Main Agent identifica necessidade de anonimização
2. Anon Agent substitui dados por marcadores genéricos
3. Validação antes da entrega final
4. Rastreabilidade para auditoria

**Exemplo**:
```
Original: "João Silva, joao@email.com, (11) 98765-4321"
Anonimizado: "NOME1, EMAIL1@dominio.com, TELEFONE1"
```

### Headers de Segurança

O Nginx configura automaticamente:
- CSP (Content Security Policy)
- XSS Protection
- Frame Options
- HTTPS (quando configurado)

### Validações

- Validação de tipos de arquivo no upload
- Sanitização de inputs SQL
- Validação de CNPJ
- Rate limiting (planejado)

---

## 🐛 Troubleshooting

### Serviço Não Inicia

```bash
# Verificar logs
docker compose logs <service-name>

# Verificar se portas estão disponíveis
netstat -tuln | grep -E '8000|8001|8002|8003|8004|8005|8080|5678|5432|5672|6379'

# Rebuild forçado
docker compose build --no-cache <service-name>
docker compose up -d <service-name>
```

### Banco de Dados Vazio

```bash
# Verificar status do PostgreSQL
docker compose exec db psql -U postgres -d notasfiscais -c "SELECT COUNT(*) FROM notasfiscais;"

# Fazer upload de notas via interface ou API
```

### Chat Não Funciona

1. Verifique se Ollama está rodando
2. Teste conexão: `curl http://<OLLAMA_HOST>/api/tags`
3. Verifique logs do nf_agent: `docker compose logs -f nf_agent`

### RabbitMQ Cheio

```bash
# Acessar management UI
open http://localhost:15672
# Login: admin / admin

# Purgar fila via CLI
docker compose exec rabbitmq rabbitmqctl purge_queue notas_fiscais
```

---

## 📚 Documentações Adicionais

Cada serviço possui documentação detalhada:

- **Load Service**: `services/load_service/DICIONARIO_DADOS.md`
- **Onboarding Service**: `services/onboarding_service/README_DLQ.md`
- **Taxes Service**: `services/taxes_service/ESCALABILIDADE.md`
- **Gov Service**: `services/gov_service/README_TRIBUTACAO.md`
- **NF Agent**: `services/nf_agent/README.md`
- **UI**: `services/ui/README.md`

---

## 📞 Suporte

Para problemas, sugestões ou dúvidas:

1. Verifique os logs: `docker compose logs -f`
2. Consulte a documentação específica do serviço
3. Verifique issues conhecidos
4. Abra uma issue no repositório

---

## 📄 Licença

MIT

---

## 🙏 Agradecimentos

Este projeto utiliza:
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent framework
- [n8n](https://n8n.io/) - Workflow automation
- [Ollama](https://ollama.ai/) - LLM local
- [Vuetify](https://vuetifyjs.com/) - Material Design components
- Diversas APIs públicas brasileiras

---

**Desenvolvido com ❤️ para gestão inteligente de notas fiscais**

