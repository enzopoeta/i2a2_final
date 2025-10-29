import express from "express";
import axios from "axios";

const GOV_SERVICE_URL = process.env.GOV_SERVICE_URL || "http://gov-service:8003";
const PORT = process.env.MCP_PORT || 8005;

const app = express();
app.use(express.json());

// Contador de chamadas para debug
let callCounter = 0;

// CORS para permitir n8n
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Health check
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    service: "gov-service-mcp",
    transport: "http",
    gov_service_url: GOV_SERVICE_URL
  });
});

// MCP Protocol: Initialize
app.post("/", async (req, res) => {
  const { method, params } = req.body;

  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`📨 MCP Request Received:`);
  console.log(`   Method: ${method}`);
  console.log(`   Params:`, JSON.stringify(params, null, 2));
  console.log(`   Headers:`, JSON.stringify(req.headers, null, 2));
  console.log(`   Body:`, JSON.stringify(req.body, null, 2));
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

  try {
    if (method === "initialize") {
      return res.json({
        jsonrpc: "2.0",
        id: req.body.id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: {
            tools: {},
          },
          serverInfo: {
            name: "gov-service-mcp",
            version: "1.0.0",
          },
        },
      });
    }

    if (method === "notifications/initialized") {
      console.log("✅ Client initialized successfully");
      return res.status(200).json({
        jsonrpc: "2.0",
        result: null,
      });
    }

    if (method === "ping") {
      return res.json({
        jsonrpc: "2.0",
        id: req.body.id,
        result: {},
      });
    }

    if (method === "tools/list") {
      const tools = [
        {
          name: "consultar_ncm",
          description: "Consulta informações tributárias de um código NCM. Retorna descrição do produto (da BrasilAPI), regime de PIS/COFINS, alíquotas de PIS, COFINS e IPI.",
          inputSchema: {
            type: "object",
            properties: {
              ncm: {
                type: "string",
                description: "Código NCM com 8 dígitos",
                pattern: "^[0-9]{8}$",
              },
            },
            required: ["ncm"],
          },
        },
        {
          name: "consultar_icms",
          description: "Consulta alíquotas e regras de ICMS para operações interestaduais. Retorna alíquotas internas, interestaduais, informações sobre ST, MVA, DIFAL e FCP.",
          inputSchema: {
            type: "object",
            properties: {
              uf_origem: {
                type: "string",
                description: "UF de origem (sigla com 2 letras maiúsculas)",
                pattern: "^[A-Z]{2}$",
              },
              uf_destino: {
                type: "string",
                description: "UF de destino (sigla com 2 letras maiúsculas)",
                pattern: "^[A-Z]{2}$",
              },
              ncm: {
                type: "string",
                description: "Código NCM com 8 dígitos",
                pattern: "^[0-9]{8}$",
              },
              tipo_operacao: {
                type: "string",
                description: "Tipo de operação",
                enum: ["VENDA_PRODUTO", "PRESTACAO_SERVICO", "DEVOLUCAO"],
                default: "VENDA_PRODUTO",
              },
            },
            required: ["uf_origem", "uf_destino", "ncm"],
          },
        },
        {
          name: "consultar_cnpj",
          description: "Consulta informações de um CNPJ em APIs públicas. Retorna dados cadastrais da empresa como razão social, endereço, atividades, etc.",
          inputSchema: {
            type: "object",
            properties: {
              cnpj: {
                type: "string",
                description: "CNPJ com 14 dígitos (pode incluir formatação)",
              },
            },
            required: ["cnpj"],
          },
        },
      ];

      return res.json({
        jsonrpc: "2.0",
        id: req.body.id,
        result: {
          tools,
        },
      });
    }

    if (method === "tools/call") {
      const { name, arguments: args } = params;
      
      callCounter++;
      console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
      console.log(`📞 Tool called #${callCounter}: ${name}`, args);
      console.log(`🆔 Request ID: ${req.body.id}`);
      console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

      let result;

      switch (name) {
        case "consultar_ncm": {
          const { ncm } = args;
          const response = await axios.get(
            `${GOV_SERVICE_URL}/ncm/consultar`,
            { params: { ncm } }
          );
          result = {
            content: [
              {
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              },
            ],
          };
          break;
        }

        case "consultar_icms": {
          const { uf_origem, uf_destino, ncm, tipo_operacao } = args;
          const response = await axios.get(
            `${GOV_SERVICE_URL}/icms/consultar_aliquotas`,
            {
              params: {
                uf_origem,
                uf_destino,
                ncm,
                tipo_operacao: tipo_operacao || "VENDA_PRODUTO",
              },
            }
          );
          result = {
            content: [
              {
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              },
            ],
          };
          break;
        }

        case "consultar_cnpj": {
          const { cnpj } = args;
          const response = await axios.get(
            `${GOV_SERVICE_URL}/cnpjinfo/${cnpj}`
          );
          result = {
            content: [
              {
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              },
            ],
          };
          break;
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }

      const response = {
        jsonrpc: "2.0",
        id: req.body.id,
        result,
      };
      
      console.log(`✅ Enviando resposta ao n8n:`, JSON.stringify(response, null, 2));
      
      return res.json(response);
    }

    // Method not supported
    return res.status(400).json({
      jsonrpc: "2.0",
      id: req.body.id,
      error: {
        code: -32601,
        message: `Method not found: ${method}`,
      },
    });
  } catch (error) {
    console.error("Error processing request:", error.message);
    const errorMessage = error.response?.data?.detail || error.message;
    return res.status(500).json({
      jsonrpc: "2.0",
      id: req.body.id,
      error: {
        code: -32603,
        message: errorMessage,
      },
    });
  }
});

// Legacy REST endpoints (manter compatibilidade)
app.get("/tools", (req, res) => {
  const tools = [
    {
      name: "consultar_ncm",
      description: "Consulta informações tributárias de um código NCM.",
    },
    {
      name: "consultar_icms",
      description: "Consulta alíquotas e regras de ICMS.",
    },
    {
      name: "consultar_cnpj",
      description: "Consulta informações de CNPJ.",
    },
  ];
  res.json({ tools });
});

app.post("/tools/call", async (req, res) => {
  try {
    const { name, arguments: args } = req.body;
    console.log(`📞 Tool called (REST): ${name}`, args);

    let result;

    switch (name) {
      case "consultar_ncm": {
        const { ncm } = args;
        const response = await axios.get(
          `${GOV_SERVICE_URL}/ncm/consultar`,
          { params: { ncm } }
        );
        result = {
          content: [
            {
              type: "text",
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
        break;
      }

      case "consultar_icms": {
        const { uf_origem, uf_destino, ncm, tipo_operacao } = args;
        const response = await axios.get(
          `${GOV_SERVICE_URL}/icms/consultar_aliquotas`,
          {
            params: {
              uf_origem,
              uf_destino,
              ncm,
              tipo_operacao: tipo_operacao || "VENDA_PRODUTO",
            },
          }
        );
        result = {
          content: [
            {
              type: "text",
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
        break;
      }

      case "consultar_cnpj": {
        const { cnpj } = args;
        const response = await axios.get(
          `${GOV_SERVICE_URL}/cnpjinfo/${cnpj}`
        );
        result = {
          content: [
            {
              type: "text",
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
        break;
      }

      default:
        return res.status(400).json({
          error: `Unknown tool: ${name}`,
          isError: true,
        });
    }

    return res.json(result);
  } catch (error) {
    console.error("Error calling tool:", error.message);
    const errorMessage = error.response?.data?.detail || error.message;
    return res.status(500).json({
      content: [
        {
          type: "text",
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    });
  }
});

app.listen(PORT, () => {
  console.log(`✅ MCP Server running on port ${PORT}`);
  console.log(`📡 Health: http://localhost:${PORT}/health`);
  console.log(`🔧 MCP Endpoint: POST http://localhost:${PORT}/`);
  console.log(`🔗 Gov Service: ${GOV_SERVICE_URL}`);
  console.log(``);
  console.log(`📚 Supported MCP methods:`);
  console.log(`   • initialize`);
  console.log(`   • tools/list`);
  console.log(`   • tools/call`);
});
