<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const showPassword = ref(false)
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
async function submit() {
  if (!form.username.trim() || !form.password) return ElMessage.warning('Enter your username and password.')
  loading.value = true
  try { await auth.signIn(form.username.trim(), form.password); await router.replace(typeof route.query.next === 'string' ? route.query.next : '/') }
  catch (error: any) { ElMessage.error(error?.response?.data?.message || 'We could not sign you in. Check your details and try again.') }
  finally { loading.value = false }
}
</script>

<template>
  <main class="login-page">
    <section class="login-showcase" aria-label="Shelfwise overview">
      <div class="showcase-top"><a class="brand brand-light" href="#"><span class="brand-mark"><el-icon><Goods /></el-icon></span><span>Shelfwise</span></a></div>
      <div class="showcase-copy"><h1>Know what's on your shelves.<br /><em>Stay ahead of what isn't.</em></h1></div>
      <div class="showcase-preview"><div class="preview-window"><div class="preview-top"><span></span><span></span><span></span><b>Stockroom workspace</b></div><div class="preview-metrics"><div><strong>Every change</strong></div><div class="preview-chart"><span style="height:45%"></span><span style="height:67%"></span><span style="height:52%"></span><span style="height:78%"></span><span style="height:62%"></span><span style="height:93%"></span><span style="height:73%"></span><span style="height:84%"></span><span style="height:67%"></span><span style="height:100%"></span><span style="height:81%"></span><span style="height:90%"></span></div></div><div class="preview-alert"><span class="alert-dot"></span><div><b>Baby spinach 120g</b></div><span class="preview-tag">REVIEW</span></div></div></div>
      <div class="showcase-foot"><span>01 <i>—</i> 03</span></div>
    </section>
    <section class="login-side"><div class="login-form-wrap"><div class="mobile-brand brand"><span class="brand-mark"><el-icon><Goods /></el-icon></span><span>Shelfwise</span></div><div class="login-heading"><h2>Welcome back</h2></div>
      <form class="login-form" @submit.prevent="submit"><label for="username">Username</label><el-input id="username" v-model="form.username" autocomplete="username" placeholder="Enter your username" size="large" /><label for="password">Password</label><el-input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" placeholder="Enter your password" size="large" @keyup.enter="submit"><template #suffix><button type="button" class="password-toggle" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword"><el-icon><View v-if="!showPassword" /><Hide v-else /></el-icon></button></template></el-input><button class="login-submit" type="submit" :disabled="loading">{{ loading ? 'Signing in…' : 'Sign in to Shelfwise' }}<el-icon><ArrowRight /></el-icon></button></form>
      <footer class="login-footer"><span>© 2026 Shelfwise</span></footer></div></section>
  </main>
</template>
