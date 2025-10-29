<template>
  <v-app>
    <!-- Menu Lateral Retrátil -->
    <v-navigation-drawer
      v-model="drawer"
      app
      :rail="rail"
      permanent
      @click="rail = false"
    >
      <v-list-item
        :prepend-avatar="rail ? undefined : '/nf-logo.png'"
        :prepend-icon="rail ? 'mdi-file-document-multiple' : undefined"
        :title="rail ? undefined : 'NF Agent'"
        :subtitle="rail ? undefined : 'Sistema Integrado'"
        nav
      >
        <template v-slot:append>
          <v-btn
            :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
            variant="text"
            @click.stop="rail = !rail"
          ></v-btn>
        </template>
      </v-list-item>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item
          v-for="item in menuItems"
          :key="item.path"
          :prepend-icon="item.icon"
          :title="item.title"
          :value="item.path"
          :to="item.path"
          :active="$route.path === item.path"
          color="primary"
        ></v-list-item>
      </v-list>

      <template v-slot:append>
        <v-divider></v-divider>
        <div class="pa-2">
          <v-chip
            :color="systemStatus.color"
            :prepend-icon="systemStatus.icon"
            size="small"
            variant="flat"
            class="w-100"
          >
            <span v-if="!rail">{{ systemStatus.text }}</span>
          </v-chip>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- Conteúdo Principal -->
    <v-main>
      <router-view />
    </v-main>

    <!-- Snackbars Globais -->
    <v-snackbar
      v-model="showSuccessSnackbar"
      color="success"
      timeout="5000"
      location="top"
    >
      <v-icon class="mr-2">mdi-check-circle</v-icon>
      {{ successMessage }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showSuccessSnackbar = false"
        >
          Fechar
        </v-btn>
      </template>
    </v-snackbar>

    <v-snackbar
      v-model="showErrorSnackbar"
      color="error"
      timeout="8000"
      location="top"
    >
      <v-icon class="mr-2">mdi-alert-circle</v-icon>
      {{ errorMessage }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showErrorSnackbar = false"
        >
          Fechar
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemStore } from './stores/system'

const systemStore = useSystemStore()
const route = useRoute()

// State
const drawer = ref(true)
const rail = ref(false)
const showSuccessSnackbar = ref(false)
const showErrorSnackbar = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Menu Items
const menuItems = computed(() => [
  { path: '/minhas-notas', title: 'Minhas Notas', icon: 'mdi-file-document-multiple' },
  { path: '/agente', title: 'Agente', icon: 'mdi-robot' },
  { path: '/informacoes', title: 'Informações', icon: 'mdi-information' }
])

// System Status
const systemStatus = computed(() => {
  if (systemStore.loadServiceStatus && systemStore.agentServiceStatus) {
    return {
      color: 'success',
      icon: 'mdi-check-circle',
      text: 'Online'
    }
  } else if (systemStore.loadServiceStatus || systemStore.agentServiceStatus) {
    return {
      color: 'warning',
      icon: 'mdi-alert-circle',
      text: 'Parcial'
    }
  } else {
    return {
      color: 'error',
      icon: 'mdi-close-circle',
      text: 'Offline'
    }
  }
})

// Check services status on mount
onMounted(() => {
  systemStore.checkServicesStatus()
})
</script>

<style scoped>
.v-list-item--active {
  font-weight: 600;
}
</style>
