import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/diagnosis', name: 'Diagnosis', component: () => import('@/views/Diagnosis.vue') },
  { path: '/cases', name: 'CaseList', component: () => import('@/views/CaseList.vue') },
  { path: '/cases/:id', name: 'CaseDetail', component: () => import('@/views/CaseDetail.vue') },
  { path: '/settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
  { path: '/compare', name: 'ModelCompare', component: () => import('@/views/ModelCompare.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
