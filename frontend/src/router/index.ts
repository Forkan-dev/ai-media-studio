import type { Component } from 'vue'
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ListChecks, Scissors, Settings, Sparkles } from 'lucide-vue-next'

declare module 'vue-router' {
  interface RouteMeta {
    title: string
    icon: Component
    nav?: 'top' | 'bottom' // shown in the sidebar
  }
}

// child routes inherit the parent's meta (title, icon)
export const routes: RouteRecordRaw[] = [
  {
    path: '/studio',
    meta: { title: 'Studio', icon: Sparkles, nav: 'top' },
    children: [
      { path: '', component: () => import('../views/StudioView.vue') },
      { path: ':slug', component: () => import('../views/BrandView.vue') },
    ],
  },
  {
    path: '/clipforge',
    component: () => import('../views/ClipForgeView.vue'),
    meta: { title: 'ClipForge', icon: Scissors, nav: 'top' },
  },
  {
    path: '/jobs',
    meta: { title: 'Jobs', icon: ListChecks, nav: 'top' },
    children: [
      { path: '', component: () => import('../views/JobsView.vue') },
      { path: ':id', component: () => import('../views/JobView.vue') },
    ],
  },
  {
    path: '/settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: 'Settings', icon: Settings, nav: 'bottom' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [{ path: '/', redirect: '/studio' }, ...routes],
})

export default router
