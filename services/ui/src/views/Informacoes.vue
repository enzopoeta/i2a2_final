<template>
  <v-container fluid class="pa-6">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-information</v-icon>
          Informações do Sistema
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card elevation="3">
          <v-card-title class="bg-info text-white">
            <v-icon class="mr-2">mdi-database</v-icon>
            Status do Banco de Dados
          </v-card-title>
          
          <v-card-text class="pa-6">
            <DatabaseStatus />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12" md="6">
        <v-card elevation="2">
          <v-card-title class="bg-primary text-white">
            <v-icon class="mr-2">mdi-server</v-icon>
            Serviços
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>
                  <v-chip 
                    :color="systemStore.loadServiceStatus ? 'success' : 'error'"
                    size="small"
                    class="mr-2"
                  >
                    <v-icon size="small" class="mr-1">
                      {{ systemStore.loadServiceStatus ? 'mdi-check' : 'mdi-close' }}
                    </v-icon>
                  </v-chip>
                  Loader Service
                </v-list-item-title>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>
                  <v-chip 
                    :color="systemStore.agentServiceStatus ? 'success' : 'error'"
                    size="small"
                    class="mr-2"
                  >
                    <v-icon size="small" class="mr-1">
                      {{ systemStore.agentServiceStatus ? 'mdi-check' : 'mdi-close' }}
                    </v-icon>
                  </v-chip>
                  Agent Service
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card elevation="2">
          <v-card-title class="bg-secondary text-white">
            <v-icon class="mr-2">mdi-chart-bar</v-icon>
            Estatísticas Rápidas
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon>mdi-file-document</v-icon>
                </template>
                <v-list-item-title>Notas Fiscais</v-list-item-title>
                <v-list-item-subtitle>{{ dbStats.notas_fiscais || 0 }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon>mdi-format-list-bulleted</v-icon>
                </template>
                <v-list-item-title>Itens</v-list-item-title>
                <v-list-item-subtitle>{{ dbStats.itens_nota_fiscal || 0 }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon>mdi-currency-usd</v-icon>
                </template>
                <v-list-item-title>Valor Total</v-list-item-title>
                <v-list-item-subtitle>R$ {{ formatCurrency(dbStats.total_value || 0) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Ações de Manutenção -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card elevation="2" color="red-lighten-5" class="border-red">
          <v-card-title class="bg-red text-white">
            <v-icon class="mr-2">mdi-alert-circle</v-icon>
            Ações de Manutenção
          </v-card-title>
          <v-card-text>
            <v-alert 
              v-if="clearSuccess"
              type="success" 
              variant="tonal" 
              closable
              @click:close="clearSuccess = false"
              class="mb-4"
            >
              <v-alert-title>Dados Removidos!</v-alert-title>
              Todas as tabelas do banco de dados foram limpas com sucesso.
            </v-alert>
            
            <v-alert 
              v-if="clearError"
              type="error" 
              variant="tonal" 
              closable
              @click:close="clearError = null"
              class="mb-4"
            >
              <v-alert-title>Erro ao Limpar Dados</v-alert-title>
              {{ clearError }}
            </v-alert>

            <v-alert type="warning" variant="tonal" class="mb-4">
              <v-alert-title>⚠️ ATENÇÃO!</v-alert-title>
              Esta ação irá remover TODOS os dados do banco de dados de forma permanente.
              Esta operação não pode ser desfeita!
            </v-alert>

            <v-btn
              color="red-darken-2"
              size="large"
              :loading="clearingData"
              :disabled="clearingData"
              @click="confirmClearData"
              class="px-8"
            >
              <v-icon class="mr-2">mdi-delete-forever</v-icon>
              Limpar Todos os Dados
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Diálogo de Confirmação -->
    <v-dialog v-model="showConfirmDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-red text-white">
          <v-icon class="mr-2">mdi-alert</v-icon>
          Confirmar Limpeza de Dados
        </v-card-title>
        <v-card-text class="pt-4">
          <p class="text-h6 mb-4">Tem certeza que deseja limpar TODOS os dados?</p>
          <p class="text-body-2">
            Esta ação irá remover permanentemente:
          </p>
          <ul class="ml-4">
            <li>Todas as notas fiscais</li>
            <li>Todos os itens das notas</li>
            <li>Todos os dados de impostos</li>
          </ul>
          <p class="text-body-2 mt-4 font-weight-bold text-red">
            Esta operação NÃO PODE ser desfeita!
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="showConfirmDialog = false"
            :disabled="clearingData"
          >
            Cancelar
          </v-btn>
          <v-btn
            color="red"
            variant="flat"
            @click="clearAllData"
            :loading="clearingData"
          >
            <v-icon class="mr-2">mdi-delete-forever</v-icon>
            Sim, Limpar Tudo
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useSystemStore } from '../stores/system'
import DatabaseStatus from '../components/DatabaseStatus.vue'
import axios from 'axios'

const systemStore = useSystemStore()

// State
const clearingData = ref(false)
const showConfirmDialog = ref(false)
const clearSuccess = ref(false)
const clearError = ref(null)

// Computed
const dbStats = computed(() => systemStore.dbStats || {})

// Methods
function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function confirmClearData() {
  showConfirmDialog.value = true
}

async function clearAllData() {
  clearingData.value = true
  clearSuccess.value = false
  clearError.value = null
  
  try {
    console.log('🗑️ Iniciando limpeza de todos os dados...')
    const response = await axios.delete('/api/load/clear-all-data')
    console.log('✅ Dados limpos com sucesso:', response.data)
    
    clearSuccess.value = true
    showConfirmDialog.value = false
    
    // Atualizar estatísticas após limpeza
    await systemStore.checkDatabaseStatus()
    
  } catch (err) {
    console.error('❌ Erro ao limpar dados:', err)
    clearError.value = err.response?.data?.detail || 'Não foi possível limpar os dados'
    showConfirmDialog.value = false
  } finally {
    clearingData.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await systemStore.checkServicesStatus()
  await systemStore.checkDatabaseStatus()
})
</script>

<style scoped>
.v-container {
  min-height: calc(100vh - 64px);
}
</style>

