/**
 * Utilitários para detecção e extração de dados de gráficos
 */

/**
 * Extrai dados de gráfico de uma mensagem
 * @param {string} message - Mensagem do agente
 * @returns {string|object|null} - Dados do gráfico ou null se não encontrado
 */
export function extractChartData(message) {
  console.log('[ChartUtils] extractChartData called with message:', message?.substring(0, 200))
  
  // 1) Identifica posição do marcador Plotly JSON
  const marker = '**PLOTLY_CHART_DATA:**'
  const idx = message.indexOf(marker)

  if (idx !== -1) {
    console.log('[ChartUtils] Found PLOTLY_CHART_DATA marker')
    // Isola tudo após o marcador
    const afterMarker = message.slice(idx + marker.length)
    
    // Procurar por blocos de código markdown
    const codeBlockRegex = /```(?:json)?\s*\n?([\s\S]*?)\n?```/
    const codeBlockMatch = afterMarker.match(codeBlockRegex)
    
    let jsonStr = null
    
    if (codeBlockMatch && codeBlockMatch[1]) {
      // Extraiu do bloco de código markdown
      jsonStr = codeBlockMatch[1].trim()
      console.log('[ChartUtils] Extracted JSON from markdown code block')
    } else {
      // Fallback para o método antigo (buscar direto pelo {)
      const firstBrace = afterMarker.indexOf('{')
      
      if (firstBrace !== -1) {
        const searchStr = afterMarker.slice(firstBrace)
        
        let depth = 0
        let inString = false
        let end = -1

        // Parser robusto para encontrar o fim do objeto JSON
        for (let i = 0; i < searchStr.length; i++) {
          const char = searchStr[i]

          if (char === '"') {
            // Verifica se a aspa é escapada
            let backslashes = 0
            let k = i - 1
            while (k >= 0 && searchStr[k] === '\\') {
              backslashes++
              k--
            }
            if (backslashes % 2 === 0) {
              inString = !inString
            }
          }
          
          if (!inString) {
            if (char === '{') {
              depth++
            } else if (char === '}') {
              depth--
              if (depth === 0) {
                end = i + 1
                break
              }
            }
          }
        }

        if (end !== -1) {
          jsonStr = searchStr.slice(0, end)
          console.log('[ChartUtils] Extracted JSON using brace matching')
        }
      }
    }
    
    // Tentar parsear o JSON extraído
    if (jsonStr) {
      let obj = null
      try {
        // Limpa escapes duplos do Python
        const cleanedJsonStr = jsonStr
          .replace(/\\\\"/g, '"')
          .replace(/\\n/g, '\n')
        obj = JSON.parse(cleanedJsonStr)
        console.log('[ChartUtils] Successfully parsed JSON (first attempt)')
      } catch (e) {
        // Tentativa mais simples
        try {
          const simplerClean = jsonStr.replace(/\\"/g, '"')
          obj = JSON.parse(simplerClean)
          console.log('[ChartUtils] Successfully parsed JSON (second attempt)')
        } catch (e2) {
          console.warn('[ChartUtils] Failed to parse JSON', { e, e2, rawJson: jsonStr.substring(0, 200) })
        }
      }
      
      // Verificar se é um objeto Plotly válido e adicionar o type se necessário
      if (obj && (obj.data || obj.layout)) {
        // Se não tem type, adicionar
        if (!obj.type) {
          obj.type = 'plotly_chart'
          console.log('[ChartUtils] Added type=plotly_chart to object')
        }
        console.log('[ChartUtils] Returning Plotly chart object')
        return obj
      }
    }
  }

  // 2. FALLBACK: HTML do Plotly
  const plotlyHtmlRegex = /<div>\s*<script[^>]*>window\.PlotlyConfig[\s\S]*?<\/script>\s*<\/div>/
  const plotlyMatch = message.match(plotlyHtmlRegex)
   
  if (plotlyMatch && plotlyMatch[0]) {
    console.log('[ChartUtils] Found Plotly HTML')
    return plotlyMatch[0]
  }
   
  // 3. FALLBACK: Data URLs base64
  const base64Regex = /data:image\/png;base64,([A-Za-z0-9+/=]+)/
  const base64Match = message.match(base64Regex)
   
  if (base64Match) {
    console.log('[ChartUtils] Found base64 image')
    return base64Match[0]
  }
   
  // 4. FALLBACK: URLs de gráfico
  const urlRegex = /https?:\/\/[^\s]+(?:chart|vis|graph)[^\s]*/gi
  const urlMatch = message.match(urlRegex)
   
  if (urlMatch && urlMatch[0]) {
    console.log('[ChartUtils] Found chart URL')
    return urlMatch[0]
  }
  
  console.log('[ChartUtils] No chart data found')
  return null
}

/**
 * Verifica se uma mensagem contém gráfico
 * @param {string} message - Mensagem do agente
 * @returns {boolean} - True se contém gráfico
 */
export function hasChart(message) {
  return extractChartData(message) !== null
}

/**
 * Detecta o tipo de agente baseado no conteúdo da mensagem
 * @param {string} message - Mensagem do agente
 * @returns {string} - Tipo do agente
 */
export function detectAgent(message) {
  const lower = message.toLowerCase()
  
  // Prioridade 1: Agente de banco de dados
  if (lower.includes('🗄️') || lower.includes('postgresql') || lower.includes('notasfiscais') ||
      lower.includes('executando query') || lower.includes('resultado da consulta') ||
      lower.includes('dados encontrados') || lower.includes('estrutura das tabelas') ||
      lower.includes('executando ferramenta') || lower.includes('execute_sql') ||
      lower.includes('connection successful') || lower.includes('query executed') ||
      (lower.includes('sql') && (lower.includes('executando') || lower.includes('resultado') || lower.includes('query'))) ||
      (lower.includes('tabela') && (lower.includes('consultando') || lower.includes('encontrada') || lower.includes('dados'))) ||
      (lower.includes('database') && (lower.includes('conectado') || lower.includes('connection'))) ||
      (lower.includes('|') && (lower.includes('table') || lower.includes('column') || lower.includes('type') || lower.includes('row'))) ||
      lower.includes('resultados da consulta') || lower.includes('linhas retornadas') ||
      lower.includes('encontrei os seguintes dados') || lower.includes('consulta ao banco')) {
    return 'db'
  }
  
  // Prioridade 2: Agente de gráficos
  if (lower.includes('📊') || lower.includes('gráfico') || lower.includes('chart') || 
      lower.includes('visualização') || lower.includes('plot') || lower.includes('dashboard') ||
      lower.includes('criando gráfico') || lower.includes('gerando visualização') ||
      lower.includes('plotly') || lower.includes('pizza') || lower.includes('barra') ||
      lower.includes('linha') || lower.includes('coluna') || lower.includes('gerado com sucesso') ||
      lower.includes('data:image/png;base64') || lower.includes('generate_pie_chart') ||
      lower.includes('generate_bar_chart') || lower.includes('generate_line_chart') ||
      lower.includes('generate_column_chart') || lower.includes('generate_area_chart') ||
      lower.includes('plotly_chart_data') ||
      (lower.includes('http') && (lower.includes('chart') || lower.includes('vis'))) ||
      lower.includes('gráfico criado') || lower.includes('visualização pronta') ||
      lower.includes('chart generated') || lower.includes('visualization complete')) {
    return 'graph'
  }
  
  // Prioridade 3: Coordenador
  if (lower.includes('🤖') || lower.includes('coordenador') || 
      lower.includes('vou consultar') || lower.includes('delegando para') ||
      lower.includes('tarefa delegada') || lower.includes('coordenando') ||
      lower.includes('{agent:') || lower.includes('vou solicitar') ||
      lower.includes('encaminhando para') || lower.includes('main_agent') ||
      lower.includes('vou dividir') || lower.includes('etapa') || lower.includes('etapas') ||
      lower.includes('primeiro precisamos') || lower.includes('vamos começar') ||
      lower.includes('para isso') || lower.includes('em seguida') ||
      (lower.includes('1.') && lower.includes('2.')) ||
      (lower.includes('primeira') && lower.includes('segunda')) ||
      (lower.includes('primeiro') && lower.includes('depois')) ||
      lower.includes('vou organizar') || lower.includes('vou delegar') ||
      lower.includes('tarefa foi dividida') || lower.includes('próximo passo')) {
    return 'main'
  }
  
  // Fallback: dados estruturados = banco
  if (lower.includes('|') && (message.split('|').length > 3)) {
    return 'db'
  }
  
  // Default: coordenador
  console.warn('Não foi possível detectar agente específico, usando main como fallback')
  return 'main'
}

/**
 * Retorna as cores do agente para Vuetify
 * @param {string} agent - Tipo do agente
 * @returns {object} - Objeto com classes de cores
 */
export function getAgentColors(agent) {
  const colors = {
    main: {
      bg: 'blue-lighten-5',
      border: 'blue-lighten-2',
      text: 'blue-darken-2',
      badge: 'blue'
    },
    db: {
      bg: 'purple-lighten-5',
      border: 'purple-lighten-2',
      text: 'purple-darken-2', 
      badge: 'purple'
    },
    graph: {
      bg: 'orange-lighten-5',
      border: 'orange-lighten-2',
      text: 'orange-darken-2',
      badge: 'orange'
    },
    user: {
      bg: 'grey-lighten-4',
      border: 'grey-lighten-2',
      text: 'grey-darken-2',
      badge: 'grey'
    }
  }
  
  return colors[agent] || colors.main
}

/**
 * Retorna o ícone do agente
 * @param {string} agent - Tipo do agente
 * @returns {string} - Ícone MDI
 */
export function getAgentIcon(agent) {
  const icons = {
    main: 'mdi-robot',
    db: 'mdi-database',
    graph: 'mdi-chart-line',
    user: 'mdi-account'
  }
  
  return icons[agent] || icons.main
}

/**
 * Retorna o nome amigável do agente
 * @param {string} agent - Tipo do agente
 * @returns {string} - Nome do agente
 */
export function getAgentName(agent) {
  const names = {
    main: 'Coordenador',
    db: 'Banco de Dados', 
    graph: 'Gráficos',
    user: 'Você'
  }
  
  return names[agent] || names.main
}

/**
 * Formata timestamp para exibição
 * @param {Date} date - Data a ser formatada
 * @returns {string} - Data formatada
 */
export function formatTime(date) {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

