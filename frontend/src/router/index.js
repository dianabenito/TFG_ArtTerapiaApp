import { createRouter, createWebHistory } from 'vue-router'
import UsersView from '../views/TempView.vue'
import ComfyView from '../views/ComfyView.vue'
import TherapistGenerationView from '../views/TherapistGenerationView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  { path: '/', component: UsersView },
  { path: '/comfy/', component: ComfyView },
  { path: '/therapist/', component: TherapistGenerationView },
  { path: '/login/', component: LoginView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
