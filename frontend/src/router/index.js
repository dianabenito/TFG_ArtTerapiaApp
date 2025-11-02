import { createRouter, createWebHistory } from 'vue-router'
import UsersView from '../views/TempView.vue'

const routes = [
  { path: '/', component: UsersView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
