import { createRouter, createWebHistory } from 'vue-router'
import UsersView from '../views/TempView.vue'
import ComfyView from '../views/ComfyView.vue'

const routes = [
  { path: '/', component: UsersView },
  { path: '/comfy/', component: ComfyView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
