import { defineStore } from 'pinia'
import { currentUser, login, logout } from '../api'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null as User | null, ready: false }),
  actions: {
    async restore() { try { this.user = await currentUser() } catch { this.user = null } finally { this.ready = true } },
    async signIn(username: string, password: string) { this.user = await login(username, password); this.ready = true },
    async signOut() { try { await logout() } finally { this.user = null } },
  },
})
