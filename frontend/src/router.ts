import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'
import LoginView from './views/LoginView.vue'
import WorkspaceView from './views/WorkspaceView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { guest: true } },
    { path: '/:pathMatch(.*)*', name: 'workspace', component: WorkspaceView, meta: { requiresAuth: true } },
  ],
})
router.beforeEach(async to => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.restore()
  if (to.meta.requiresAuth && !auth.user) return { name: 'login', query: { next: to.fullPath } }
  const view=String(to.query.view||'overview')
  if(auth.user?.role==='CLERK'&&['warnings','reports','team','settings'].includes(view))return {path:'/',query:{view:'inventory'}}
  if(auth.user?.role==='MANAGER'&&['team','settings'].includes(view))return {path:'/',query:{view:'inventory'}}
  if (to.name === 'login' && auth.user) return { path: '/' }
})
