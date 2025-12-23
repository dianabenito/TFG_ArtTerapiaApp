import { createRouter, createWebHistory } from 'vue-router'
import SignupView from '../views/SignupView.vue'
import TherapistGenerationView from '../views/TherapistGenerationView.vue'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import CanvasView from '../views/CanvasView.vue'
import GenerationView from '../views/GenerationView.vue'
import CalendarView from '../views/CalendarView.vue'
import SessionView from '../views/SessionView.vue'

const routes = [
  { path: '/', component: LoginView },
  { path: '/signup/', component: SignupView },
  { path: '/home/', component: HomeView },
  { path: '/canvas/', component: CanvasView },
  { path: '/generation/', component: GenerationView },
  { path: '/freeimages/', component: SessionView },
  // session-specific routes (use sessionId param)
  { path: '/session/:sessionId/patient', component: GenerationView, props: true },
  { path: '/session/:sessionId/patient/canvas', component: CanvasView, props: true },
  { path: '/session/:sessionId/therapist', component: TherapistGenerationView, props: true },
  { path: '/session/:sessionId', component: SessionView, props: true },
  { path: '/calendar', component: CalendarView }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
