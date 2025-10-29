<template>
  <v-container fluid class="pa-6">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-cloud-upload</v-icon>
          Upload de Notas Fiscais
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card elevation="3">
          <v-card-title class="bg-primary text-white">
            <v-icon class="mr-2">mdi-file-upload</v-icon>
            Enviar Arquivos
          </v-card-title>
          
          <v-card-text class="pa-6">
            <FileUpload 
              @upload-success="handleUploadSuccess"
              @upload-error="handleUploadError"
              :disabled="!systemStore.loadServiceStatus"
            />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card elevation="2">
          <v-card-title class="bg-info text-white">
            <v-icon class="mr-2">mdi-help-circle</v-icon>
            Instruções
          </v-card-title>
          
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title class="text-wrap">
                  <v-icon size="small" class="mr-2">mdi-file-xml</v-icon>
                  Arquivos XML individuais
                </v-list-item-title>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-wrap">
                  <v-icon size="small" class="mr-2">mdi-zip-box</v-icon>
                  Arquivos ZIP com CSVs (Cabecalho e Itens)
                </v-list-item-title>
              </v-list-item>
              <v-list-item>
                <v-list-item-title class="text-wrap">
                  <v-icon size="small" class="mr-2">mdi-robot</v-icon>
                  Classificação automática via IA
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSystemStore } from '../stores/system'
import FileUpload from '../components/FileUpload.vue'

const systemStore = useSystemStore()
const router = useRouter()

// Reactive data
const showSuccessSnackbar = ref(false)
const showErrorSnackbar = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Methods
function handleUploadSuccess(data) {
  successMessage.value = `Upload realizado com sucesso! ${data.processed_files || 1} arquivo(s) processado(s).`
  showSuccessSnackbar.value = true
  
  // Refresh database status
  setTimeout(async () => {
    await systemStore.checkDatabaseStatus()
  }, 2000)
}

function handleUploadError(error) {
  errorMessage.value = `Erro no upload: ${error}`
  showErrorSnackbar.value = true
}
</script>

<style scoped>
.v-container {
  min-height: calc(100vh - 64px);
}
</style>

