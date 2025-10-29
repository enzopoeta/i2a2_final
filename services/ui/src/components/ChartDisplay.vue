<template>
  <div v-if="shouldShowChart" class="chart-display" :class="className">
    <h3 v-if="title" class="text-h6 mb-3 text-grey-darken-2">
      {{ title }}
    </h3>
    <v-card class="chart-container" elevation="2">
      <v-card-text class="pa-4">
        <!-- Plotly Chart (JSON Data) -->
        <div v-if="isPlotlyJson" class="plotly-container">
          <div ref="plotlyDiv" class="plotly-div" style="width: 100%; height: 500px;"></div>
        </div>
        
        <!-- Plotly Chart (HTML) -->
        <div 
          v-else-if="isPlotlyHtml" 
          class="plotly-html-container"
          v-html="chartData"
          style="min-height: 400px;"
        />
        
        <!-- Base64 Image -->
        <div v-else-if="isBase64Image" class="text-center">
          <img
            :src="chartData"
            :alt="title || 'Gráfico gerado'"
            class="max-width-full"
            style="max-height: 600px; object-fit: contain;"
            @error="onImageError"
          />
        </div>
        
        <!-- Chart URL -->
        <div v-else-if="isChartUrl" class="chart-url-container">
          <iframe
            :src="chartData"
            :title="title || 'Gráfico externo'"
            class="chart-iframe"
            style="width: 100%; height: 600px; min-height: 400px; border: none; border-radius: 8px;"
            @error="onIframeError"
          />
          <div class="mt-2 text-center">
            <v-btn
              :href="chartData"
              target="_blank"
              rel="noopener noreferrer"
              variant="text"
              color="primary"
              prepend-icon="mdi-open-in-new"
              size="small"
            >
              Abrir gráfico em nova aba
            </v-btn>
          </div>
        </div>
        
        <!-- Loading State -->
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4 text-grey-darken-1">Carregando gráfico...</p>
        </div>
        
        <!-- Error State -->
        <div v-if="error" class="text-center py-8">
          <v-icon color="error" size="64">mdi-chart-line-variant</v-icon>
          <p class="mt-4 text-error">{{ error }}</p>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps({
  chartData: {
    type: [String, Object],
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  className: {
    type: String,
    default: ''
  }
})

const loading = ref(false)
const error = ref('')
const plotlyDiv = ref(null)

// Computed properties for chart type detection
const isPlotlyJson = computed(() => {
  return typeof props.chartData === 'object' && 
    props.chartData !== null && 
    'type' in props.chartData && 
    props.chartData.type === 'plotly_chart'
})

const isPlotlyHtml = computed(() => {
  return typeof props.chartData === 'string' && 
    props.chartData.includes('<div') && 
    (props.chartData.includes('plotly') || 
     props.chartData.includes('Plotly') ||
     props.chartData.includes('plotly-div'))
})

const isBase64Image = computed(() => {
  return typeof props.chartData === 'string' && 
    props.chartData.startsWith('data:image/')
})

const isChartUrl = computed(() => {
  return typeof props.chartData === 'string' && 
    props.chartData.startsWith('http') && 
    (props.chartData.includes('chart') || props.chartData.includes('vis'))
})

const shouldShowChart = computed(() => {
  return isPlotlyJson.value || isPlotlyHtml.value || isBase64Image.value || isChartUrl.value
})

// Função para renderizar gráfico Plotly
const renderPlotlyChart = async () => {
  if (!isPlotlyJson.value || !plotlyDiv.value) return
  
  try {
    loading.value = true
    error.value = ''
    
    const layout = {
      ...props.chartData.layout,
      autosize: true,
      width: undefined,
      height: 500,
      margin: { t: 80, b: 60, l: 60, r: 40 },
      font: {
        family: 'Roboto, sans-serif',
        size: 12
      },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    }
    
    const config = {
      ...props.chartData.config,
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
      locale: 'pt-BR'
    }
    
    await Plotly.newPlot(plotlyDiv.value, props.chartData.data, layout, config)
    loading.value = false
  } catch (err) {
    console.error('Erro ao renderizar gráfico Plotly:', err)
    error.value = 'Erro ao renderizar gráfico'
    loading.value = false
  }
}

const onImageError = (event) => {
  console.error('Erro ao carregar gráfico base64:', event)
  error.value = 'Erro ao carregar imagem do gráfico'
  event.target.style.display = 'none'
}

const onIframeError = (event) => {
  console.error('Erro ao carregar gráfico via URL:', event)
  error.value = 'Erro ao carregar gráfico externo'
}

// Watch for changes in chart data
watch(() => props.chartData, async (newData) => {
  error.value = ''
  loading.value = false
  
  if (newData && isPlotlyJson.value) {
    // Validate Plotly data structure
    if (!newData.data || !Array.isArray(newData.data)) {
      error.value = 'Dados do gráfico inválidos'
      return
    }
    
    // Aguarda o próximo tick para garantir que o DOM foi atualizado
    await nextTick()
    renderPlotlyChart()
  }
}, { immediate: true })

onMounted(async () => {
  console.log('ChartDisplay mounted with data:', props.chartData)
  
  if (isPlotlyJson.value) {
    await nextTick()
    renderPlotlyChart()
  }
})
</script>

<style scoped>
.chart-display {
  width: 100%;
  margin: 16px 0;
}

.chart-container {
  background: white;
  border-radius: 8px;
}

.plotly-container {
  width: 100%;
  height: 500px;
}

.plotly-div {
  width: 100%;
  height: 500px;
}

.plotly-html-container {
  width: 100%;
  min-height: 400px;
}

.chart-iframe {
  border-radius: 8px;
}

.max-width-full {
  max-width: 100%;
  height: auto;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .plotly-container,
  .plotly-div {
    height: 400px;
  }
  
  .chart-iframe {
    height: 400px !important;
  }
}
</style>

