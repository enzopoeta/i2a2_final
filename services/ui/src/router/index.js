// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Informacoes from '../views/Informacoes.vue'
import MinhasNotas from '../views/MinhasNotas.vue'
import DetalhamentoNota from '../views/DetalhamentoNota.vue'
import AgenteNotas from '../views/AgenteNotas.vue'

const routes = [
  {
    path: '/',
    redirect: '/minhas-notas'
  },
  {
    path: '/informacoes',
    name: 'Informacoes',
    component: Informacoes,
    meta: { title: 'Informações', icon: 'mdi-information' }
  },
  {
    path: '/minhas-notas',
    name: 'MinhasNotas',
    component: MinhasNotas,
    meta: { title: 'Minhas Notas', icon: 'mdi-file-document-multiple' }
  },
  {
    path: '/notas/:chaveAcesso',
    name: 'DetalhamentoNota',
    component: DetalhamentoNota,
    meta: { title: 'Detalhamento da Nota', icon: 'mdi-file-document', hideInMenu: true }
  },
  {
    path: '/agente',
    name: 'AgenteNotas',
    component: AgenteNotas,
    meta: { title: 'Agente de Notas Fiscais', icon: 'mdi-robot' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

