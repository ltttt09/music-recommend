<template>
  <div class="container">
    <div class="auth-card">
      <h1>登录</h1>
      <form @submit.prevent="doLogin">
        <label>用户名</label>
        <input v-model="username" placeholder="输入用户名" required />
        <label>密码</label>
        <input v-model="password" type="password" placeholder="输入密码" required />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <p class="switch">还没有账号？<router-link to="/register">去注册</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api.js'
import { auth } from '../auth.js'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function doLogin() {
  loading.value = true; error.value = ''
  try {
    const data = await api.login(username.value, password.value)
    auth.login(data.token, data.user_id, data.username)
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-card { max-width: 380px; margin: 60px auto; background: var(--color-surface); border-radius: var(--radius); padding: 32px; }
.auth-card h1 { font-size: 22px; margin-bottom: 24px; text-align: center; }
form { display: flex; flex-direction: column; gap: 8px; }
label { font-size: 13px; font-weight: 600; color: var(--color-text-muted); }
input { padding: 10px 14px; }
.error { color: var(--color-dislike); font-size: 13px; }
.switch { text-align: center; font-size: 13px; color: var(--color-text-muted); margin-top: 16px; }
</style>