<template>
  <v-container fluid class="pa-6">
    <v-row>
      <v-col cols="12" class="d-flex justify-space-between align-center">
        <h1 class="text-h4 mb-0">
          <v-icon class="mr-2">mdi-file-document-multiple</v-icon>
          Minhas Notas Fiscais
        </h1>
        <v-btn
          color="primary"
          size="large"
          @click="showUploadDialog = true"
          :disabled="!systemStore.loadServiceStatus"
        >
          <v-icon class="mr-2">mdi-plus-circle</v-icon>
          Adicionar Nova Nota
        </v-btn>
      </v-col>
    </v-row>

    <!-- Filtros -->
    <v-row>
      <v-col cols="12" md="4">
        <v-text-field
          v-model="search"
          label="Buscar"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          clearable
          hint="Busque por chave, número da NF, fornecedor ou produto"
          persistent-hint
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="filterClassificacao"
          :items="classificacaoOptions"
          label="Classificação"
          variant="outlined"
          density="compact"
          clearable
          hint="Filtrar por tipo de operação"
          persistent-hint
        ></v-select>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="sortBy"
          :items="sortOptions"
          label="Ordenar por"
          variant="outlined"
          density="compact"
        ></v-select>
      </v-col>
      <v-col cols="12" md="2">
        <v-btn
          color="primary"
          block
          @click="loadNotas"
          :loading="loading"
        >
          <v-icon class="mr-2">mdi-refresh</v-icon>
          Atualizar
        </v-btn>
      </v-col>
    </v-row>

    <!-- Lista de Notas -->
    <v-row v-if="loading && notas.length === 0">
      <v-col cols="12" class="text-center">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        ></v-progress-circular>
        <p class="mt-4">Carregando notas fiscais...</p>
      </v-col>
    </v-row>

    <v-row v-else-if="!loading && notas.length === 0">
      <v-col cols="12">
        <v-alert type="info" variant="tonal">
          <v-alert-title>Nenhuma nota fiscal encontrada</v-alert-title>
          Faça o upload de notas fiscais na seção "Upload".
        </v-alert>
      </v-col>
    </v-row>

    <v-row v-else>
      <v-col
        v-for="nota in paginatedNotas"
        :key="nota.chave_acesso"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card
          elevation="2"
          hover
          @click="goToDetalhamento(nota.chave_acesso)"
          class="nota-card"
        >
          <v-card-title class="text-h6">
            NF {{ nota.numero_nf }}
          </v-card-title>
          <v-card-subtitle>
            {{ formatDate(nota.data_emissao) }}
          </v-card-subtitle>

          <v-card-text>
            <v-list density="compact">
              <v-list-item density="compact">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-domain</v-icon>
                </template>
                <v-list-item-title class="text-caption">Emitente</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">
                  {{ nota.emit_xnome || 'N/A' }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item density="compact">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-account</v-icon>
                </template>
                <v-list-item-title class="text-caption">Destinatário</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">
                  {{ nota.dest_xnome || 'N/A' }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item density="compact">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-package-variant</v-icon>
                </template>
                <v-list-item-title class="text-caption">Itens</v-list-item-title>
                <v-list-item-subtitle class="text-body-2">
                  {{ nota.total_items || 0 }} item(ns)
                </v-list-item-subtitle>
              </v-list-item>

              <v-divider class="my-2"></v-divider>

              <v-list-item density="compact">
                <template v-slot:prepend>
                  <v-icon size="small" color="success">mdi-currency-usd</v-icon>
                </template>
                <v-list-item-title class="text-caption">Valor Total</v-list-item-title>
                <v-list-item-subtitle class="text-h6 text-success">
                  R$ {{ formatCurrency(nota.valor_total) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              variant="text"
              size="small"
            >
              Ver Detalhes
              <v-icon class="ml-1">mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Paginação -->
    <v-row v-if="notas.length > 0">
      <v-col cols="12" class="d-flex justify-center">
        <v-pagination
          v-model="currentPage"
          :length="totalPages"
          :total-visible="7"
          @update:modelValue="scrollToTop"
        ></v-pagination>
      </v-col>
    </v-row>

    <!-- Upload Dialog -->
    <v-dialog
      v-model="showUploadDialog"
      max-width="800px"
      persistent
    >
      <v-card>
        <v-card-title class="bg-primary text-white d-flex align-center">
          <v-icon class="mr-2">mdi-file-upload</v-icon>
          <span>Adicionar Nova Nota Fiscal</span>
          <v-spacer></v-spacer>
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="closeUploadDialog"
          />
        </v-card-title>

        <v-card-text class="pa-6">
          <v-alert
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            <div class="text-subtitle-2 mb-2">Formatos Aceitos:</div>
            <v-list density="compact">
              <v-list-item density="compact">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-file-xml</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Arquivos XML individuais de Nota Fiscal
                </v-list-item-title>
              </v-list-item>
              <v-list-item density="compact">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-zip-box</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Arquivos ZIP contendo CSVs (Cabeçalho e Itens)
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-alert>

          <FileUpload 
            @upload-success="handleUploadSuccess"
            @upload-error="handleUploadError"
            :disabled="!systemStore.loadServiceStatus"
          />
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeUploadDialog"
          >
            Fechar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
    <v-snackbar
      v-model="showSuccessSnackbar"
      color="success"
      timeout="5000"
      location="top"
    >
      <v-icon class="mr-2">mdi-check-circle</v-icon>
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="showSuccessSnackbar = false">Fechar</v-btn>
      </template>
    </v-snackbar>

    <!-- Error Snackbar -->
    <v-snackbar
      v-model="showErrorSnackbar"
      color="error"
      timeout="8000"
      location="top"
    >
      <v-icon class="mr-2">mdi-alert-circle</v-icon>
      {{ errorMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="showErrorSnackbar = false">Fechar</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSystemStore } from '../stores/system'
import axios from 'axios'
import FileUpload from '../components/FileUpload.vue'

const router = useRouter()
const systemStore = useSystemStore()

// State
const notas = ref([])
const loading = ref(false)
const search = ref('')
const filterClassificacao = ref(null)
const sortBy = ref('data_desc')
const currentPage = ref(1)
const itemsPerPage = ref(9)

// Upload state
const showUploadDialog = ref(false)
const showSuccessSnackbar = ref(false)
const showErrorSnackbar = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Classificação Options
const classificacaoOptions = [
  { title: 'Todas', value: null },
  { title: 'Compra', value: 'COMPRA' },
  { title: 'Venda', value: 'VENDA' },
  { title: 'Serviço', value: 'SERVICO' }
]

// Sort Options
const sortOptions = [
  { title: 'Data (mais recente)', value: 'data_desc' },
  { title: 'Data (mais antiga)', value: 'data_asc' },
  { title: 'Valor (maior)', value: 'valor_desc' },
  { title: 'Valor (menor)', value: 'valor_asc' },
  { title: 'Número NF (crescente)', value: 'nf_asc' },
  { title: 'Número NF (decrescente)', value: 'nf_desc' }
]

// Computed
const filteredNotas = computed(() => {
  let filtered = [...notas.value]

  // Aplicar busca
  if (search.value) {
    const searchLower = search.value.toLowerCase()
    filtered = filtered.filter(nota => 
      nota.chave_acesso?.toLowerCase().includes(searchLower) ||
      nota.numero_nf?.toString().includes(searchLower) ||
      nota.emit_xnome?.toLowerCase().includes(searchLower) ||
      nota.dest_xnome?.toLowerCase().includes(searchLower)
    )
  }

  // Aplicar filtro de classificação
  if (filterClassificacao.value) {
    filtered = filtered.filter(nota => 
      nota.classificacao === filterClassificacao.value
    )
  }

  // Aplicar ordenação
  switch (sortBy.value) {
    case 'data_desc':
      filtered.sort((a, b) => new Date(b.data_emissao) - new Date(a.data_emissao))
      break
    case 'data_asc':
      filtered.sort((a, b) => new Date(a.data_emissao) - new Date(b.data_emissao))
      break
    case 'valor_desc':
      filtered.sort((a, b) => (b.valor_total || 0) - (a.valor_total || 0))
      break
    case 'valor_asc':
      filtered.sort((a, b) => (a.valor_total || 0) - (b.valor_total || 0))
      break
    case 'nf_asc':
      filtered.sort((a, b) => (a.numero_nf || 0) - (b.numero_nf || 0))
      break
    case 'nf_desc':
      filtered.sort((a, b) => (b.numero_nf || 0) - (a.numero_nf || 0))
      break
  }

  return filtered
})

const paginatedNotas = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredNotas.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredNotas.value.length / itemsPerPage.value)
})

// Methods
async function loadNotas() {
  loading.value = true
  console.log('🔍 [MinhasNotas] Iniciando carregamento de notas...')
  try {
    console.log('📡 [MinhasNotas] Fazendo requisição para /api/notas')
    const response = await axios.get('/api/notas')
    console.log('✅ [MinhasNotas] Resposta recebida:', response.data)
    console.log('📊 [MinhasNotas] Quantidade de notas:', response.data.notas?.length || 0)
    notas.value = response.data.notas || []
    console.log('💾 [MinhasNotas] Notas armazenadas:', notas.value.length)
  } catch (error) {
    console.error('❌ [MinhasNotas] Erro ao carregar notas:', error)
    console.error('❌ [MinhasNotas] Detalhes do erro:', error.response || error.message)
    notas.value = []
  } finally {
    loading.value = false
    console.log('🏁 [MinhasNotas] Carregamento finalizado. Total:', notas.value.length)
  }
}

function goToDetalhamento(chaveAcesso) {
  router.push(`/notas/${chaveAcesso}`)
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('pt-BR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(date)
}

function formatCurrency(value) {
  if (!value) return '0,00'
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Upload handlers
function handleUploadSuccess(data) {
  successMessage.value = `Upload realizado com sucesso! ${data.processed_files || 1} arquivo(s) processado(s).`
  showSuccessSnackbar.value = true
  closeUploadDialog()
  
  // Refresh notes list and database status
  setTimeout(async () => {
    await systemStore.checkDatabaseStatus()
    await loadNotas()
  }, 1500)
}

function handleUploadError(error) {
  errorMessage.value = `Erro no upload: ${error}`
  showErrorSnackbar.value = true
}

function closeUploadDialog() {
  showUploadDialog.value = false
}

// Watchers
watch([search, sortBy, filterClassificacao], () => {
  currentPage.value = 1
})

// Lifecycle
onMounted(() => {
  loadNotas()
})
</script>

<style scoped>
.v-container {
  min-height: calc(100vh - 64px);
}

.nota-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.nota-card:hover {
  transform: translateY(-4px);
}
</style>

