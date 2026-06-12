<template>
  <div class="container">
    <div class="auth-card">
      <h1>注册</h1>
      <form @submit.prevent="doRegister">
        <label>用户名</label>
        <input v-model="username" placeholder="至少3个字符" required />
        <label>显示名称</label>
        <input v-model="displayName" placeholder="可选" />
        <label>密码</label>
        <input v-model="password" type="password" placeholder="至少4个字符" required />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <p class="switch">已有账号？<router-link to="/login">去登录</router-link></p>
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
const displayName = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function doRegister() {
  loading.value = true; error.value = ''
  try {
    const reg = await api.register(username.value, password.value, displayName.value)
    if (reg.user_id) {
      // Auto-login after registration
      const data = await api.login(username.value, password.value)
      auth.login(data.token, data.user_id, data.username)
      router.push('/')
    } else {
      router.push('/login')
    }
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