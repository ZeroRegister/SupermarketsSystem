import axios from 'axios'
import type { Category, Dashboard, Page, Product, Supplier, Transaction, User, Warning } from './types'

export const api = axios.create({ baseURL: '/api', withCredentials: true, headers: { 'Content-Type': 'application/json' } })
let csrfToken = ''
api.interceptors.request.use(config => {
  if (csrfToken && !['get', 'head', 'options'].includes((config.method || 'get').toLowerCase())) config.headers['X-XSRF-TOKEN'] = csrfToken
  return config
})
api.interceptors.response.use(r => r, error => {
  if (error.response?.status === 401 && !location.pathname.startsWith('/login')) window.dispatchEvent(new Event('shelfwise:unauthenticated'))
  return Promise.reject(error)
})
export async function prepareCsrf() { const r = await api.get<{ token: string }>('/auth/csrf'); csrfToken = r.data.token }
export async function login(username: string, password: string) { await prepareCsrf(); const r = await api.post<User>('/auth/login', { username, password }); return r.data }
export async function currentUser() { return (await api.get<User>('/auth/me')).data }
export async function logout() { await api.post('/auth/logout') }
export async function products(params: Record<string, unknown> = {}) { return (await api.get<Page<Product>>('/products', { params })).data }
export async function transactions(params: Record<string, unknown> = {}) { return (await api.get<Page<Transaction>>('/transactions', { params })).data }
export async function warnings(params: Record<string, unknown> = {}) { return (await api.get<Page<Warning>>('/warnings', { params })).data }
export async function dashboard() { return (await api.get<Dashboard>('/dashboard')).data }
export async function stockSummary() { return (await api.get<Dashboard>('/stock-summary')).data }
export async function categories() { return (await api.get<Category[]>('/categories')).data }
export async function suppliers() { return (await api.get<Supplier[]>('/suppliers')).data }
export async function users() { return (await api.get<User[]>('/users')).data }
