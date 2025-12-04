import { createRouter, createWebHistory } from 'vue-router'
import UsersView from '../views/TempView.vue'
import ComfyView from '../views/ComfyView.vue'
import TherapistGenerationView from '../views/TherapistGenerationView.vue'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import CanvasView from '../views/CanvasView.vue'
import GenerationView from '../views/GenerationView.vue'

const routes = [
  { path: '/', component: UsersView },
  { path: '/therapist/', component: TherapistGenerationView },
  { path: '/login/', component: LoginView },
  { path: '/home/', component: HomeView },
  { path: '/canvas/', component: CanvasView },
  { path: '/generation/', component: GenerationView },
  // session-specific routes (use sessionId param)
  { path: '/session/:sessionId/patient', component: GenerationView, props: true },
  { path: '/session/:sessionId/therapist', component: TherapistGenerationView, props: true },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
