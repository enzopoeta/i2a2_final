<template>
  <v-container fluid class="pa-0 fill-height">
    <v-row no-gutters class="fill-height">
      <v-col cols="12" class="fill-height">
        <v-card elevation="0" class="fill-height d-flex flex-column">
          <v-card-title class="bg-primary text-white d-flex align-center">
            <v-icon class="mr-2">mdi-robot</v-icon>
            <span class="flex-grow-0">Agente de Notas Fiscais</span>
            <v-spacer></v-spacer>
            
            <!-- Botões do Chat -->
            <v-btn
              icon
              variant="text"
              size="small"
              @click="showTaskHistory = !showTaskHistory"
              class="mr-2"
              title="Histórico de Tarefas"
            >
              <v-icon>mdi-history</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              size="small"
              @click="resetAgents"
              :loading="resettingAgents"
              class="mr-2"
              title="Reiniciar time de agentes"
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
            
            <!-- Status Chip -->
            <v-chip
              :color="systemStore.chatEnabled ? 'success' : 'error'"
              size="small"
              variant="flat"
            >
              <v-icon size="small" class="mr-1">
                {{ systemStore.chatEnabled ? 'mdi-check' : 'mdi-close' }}
              </v-icon>
              {{ systemStore.chatEnabled ? 'Online' : 'Offline' }}
            </v-chip>
          </v-card-title>

          <v-card-text class="flex-grow-1 pa-0">
            <AgentChat 
              :enabled="systemStore.chatEnabled"
              :fullscreen="true"
              :show-task-history="showTaskHistory"
              :resetting-agents="resettingAgents"
              @update:show-task-history="showTaskHistory = $event"
              @reset-agents="handleResetAgents"
              :key="chatKey"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSystemStore } from '../stores/system'
import AgentChat from '../components/AgentChat.vue'
import axios from 'axios'

const systemStore = useSystemStore()
const chatKey = ref(0)
const showTaskHistory = ref(false)
const resettingAgents = ref(false)

// Methods
async function handleResetAgents() {
  resettingAgents.value = true
  try {
    const response = await axios.post('/api/agent/restart-agents/')
    if (response.data.status === 'ok') {
      console.log('✅ Time de agentes reiniciado com sucesso.')
    } else {
      console.error('❌ Falha ao reiniciar agentes:', response.data.message)
    }
  } catch (error) {
    console.error('❌ Erro ao reiniciar agentes:', error.message)
  } finally {
    resettingAgents.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await systemStore.checkServicesStatus()
})
</script>

<style scoped>
.v-container {
  height: calc(100vh - 64px);
  max-height: calc(100vh - 64px);
}

.fill-height {
  height: 100%;
}
</style>

