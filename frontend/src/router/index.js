import { createRouter, createWebHistory } from 'vue-router'
import UsersView from '../views/TempView.vue'
import ComfyView from '../views/ComfyView.vue'
import TherapistGenerationView from '../views/TherapistGenerationView.vue'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'

const routes = [
  { path: '/', component: UsersView },
  { path: '/comfy/', component: ComfyView },
  { path: '/therapist/', component: TherapistGenerationView },
  { path: '/login/', component: LoginView },
  { path: '/home/', component: HomeView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
