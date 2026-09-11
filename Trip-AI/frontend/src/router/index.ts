import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/Home.vue') },
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue') },
  { path: '/register', name: 'register', component: () => import('@/views/Register.vue') },
  { path: '/result', name: 'result', component: () => import('@/views/Result.vue') },
  {
    path: '/my-trips',
    name: 'my-trips',
    component: () => import('@/views/MyTrips.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/my-trips/:id',
    name: 'trip-detail',
    component: () => import('@/views/Result.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/share/:token', name: 'share', component: () => import('@/views/ShareView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
