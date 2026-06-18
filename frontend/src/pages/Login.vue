<template>
  <div class="login-page">
    <div class="bg-decor" aria-hidden="true">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
    </div>

    <section class="login-wrap" aria-label="账号登录与注册">
      <aside class="brand">
        <div class="brand-logo">🎵</div>
        <div class="brand-name">SoundMind</div>
        <p class="brand-desc">发现你的下一首最爱<br>智能推荐 · 多语种曲库 · 个性化收藏</p>
        <div class="brand-features">
          <div class="brand-feat"><span>🧠</span> 6 种推荐模型混合</div>
          <div class="brand-feat"><span>🌍</span> 多语种音乐发现</div>
          <div class="brand-feat"><span>📋</span> 歌单 · 收藏 · 评论</div>
        </div>
      </aside>

      <div class="form-panel">
        <div class="mode-tabs">
          <button type="button" :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</button>
          <button type="button" :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</button>
        </div>

        <div class="form-title">
          <h1>{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</h1>
          <p>{{ mode === 'login' ? '登录后继续获取你的音乐推荐' : '注册后系统会自动登录并进入首页' }}</p>
        </div>

        <form v-if="mode === 'login'" @submit.prevent="doLogin">
          <div class="field">
            <label>账号</label>
            <input v-model.trim="loginForm.username" type="text" placeholder="输入账号" autocomplete="username" />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="loginForm.password" type="password" placeholder="输入密码" autocomplete="current-password" />
          </div>
          <div class="options">
            <label><input v-model="rememberMe" type="checkbox"> 记住我</label>
            <button type="button" class="link-btn" @click="showForgotHint">忘记密码？</button>
          </div>
          <p v-if="error" class="error-msg">{{ error }}</p>
          <button type="submit" class="btn-submit" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <form v-else @submit.prevent="doRegister">
          <div class="field">
            <label>账号</label>
            <input v-model.trim="registerForm.username" type="text" placeholder="至少 3 个字符" autocomplete="username" />
          </div>
          <div class="field">
            <label>显示名称</label>
            <input v-model.trim="registerForm.displayName" type="text" placeholder="可选" autocomplete="name" />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="registerForm.password" type="password" placeholder="至少 4 个字符" autocomplete="new-password" />
          </div>
          <p v-if="error" class="error-msg">{{ error }}</p>
          <button type="submit" class="btn-submit" :disabled="loading">
            {{ loading ? '注册中...' : '注册并登录' }}
          </button>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api.js'
import { auth } from '../auth.js'

const router = useRouter()
const mode = ref('login')
const rememberMe = ref(localStorage.getItem('remember_login') === '1')
const loading = ref(false)
const error = ref('')

const loginForm = reactive({
  username: localStorage.getItem('remembered_username') || '',
  password: '',
})

const registerForm = reactive({
  username: '',
  displayName: '',
  password: '',
})

function switchMode(nextMode) {
  mode.value = nextMode
  error.value = ''
}

function validateAccount(username, password) {
  if (!username || username.length < 3) return '账号至少需要 3 个字符'
  if (!password || password.length < 4) return '密码至少需要 4 个字符'
  return ''
}

function persistRememberedAccount(username) {
  if (rememberMe.value) {
    localStorage.setItem('remember_login', '1')
    localStorage.setItem('remembered_username', username)
  } else {
    localStorage.removeItem('remember_login')
    localStorage.removeItem('remembered_username')
  }
}

async function doLogin() {
  error.value = validateAccount(loginForm.username, loginForm.password)
  if (error.value) return
  loading.value = true
  try {
    const data = await api.login(loginForm.username, loginForm.password)
    auth.login(data.token, data.user_id, data.username)
    persistRememberedAccount(loginForm.username)
    router.push('/')
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  error.value = validateAccount(registerForm.username, registerForm.password)
  if (error.value) return
  loading.value = true
  try {
    await api.register(registerForm.username, registerForm.password, registerForm.displayName || registerForm.username)
    const data = await api.login(registerForm.username, registerForm.password)
    auth.login(data.token, data.user_id, data.username)
    router.push('/')
  } catch (e) {
    error.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}

function showForgotHint() {
  error.value = '当前演示系统暂不支持找回密码，请重新注册或联系管理员处理'
}
</script>

<style>
.login-page {
  position: relative;
  min-height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 36px 20px;
  overflow: hidden;
}

.bg-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: .12;
}

.bg-circle.c1 {
  width: 540px;
  height: 540px;
  background: var(--color-primary);
  top: -22%;
  left: -14%;
}

.bg-circle.c2 {
  width: 440px;
  height: 440px;
  background: var(--color-accent);
  right: -12%;
  bottom: -18%;
}

.login-wrap {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 880px;
  min-height: 520px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid var(--color-border);
  border-radius: 24px;
  overflow: hidden;
  background: var(--color-surface);
  box-shadow: var(--shadow);
}

.brand {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 36px;
  text-align: center;
  overflow: hidden;
  background: linear-gradient(160deg, var(--color-bg), var(--color-surface-hover), var(--color-bg));
}

.brand::before {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--color-primary-light), transparent);
  top: -100px;
  right: -100px;
  opacity: .45;
}

.brand-logo {
  position: relative;
  z-index: 1;
  font-size: 48px;
  font-weight: 900;
  margin-bottom: 12px;
}

.brand-name {
  position: relative;
  z-index: 1;
  font-size: 22px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--color-accent), var(--color-primary));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-desc {
  position: relative;
  z-index: 1;
  max-width: 280px;
  margin-top: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.7;
}

.brand-features {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 28px;
}

.brand-feat {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.brand-feat span {
  font-size: 16px;
}

.form-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 40px;
  background: var(--color-surface);
}

.mode-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  padding: 4px;
  border-radius: 12px;
  background: var(--color-bg);
}

.mode-tabs button {
  flex: 1;
  border: none;
  border-radius: 10px;
  padding: 9px;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 700;
  transition: color .2s, background .2s, box-shadow .2s;
}

.mode-tabs button.active {
  color: var(--color-text);
  background: var(--color-surface);
  box-shadow: 0 1px 3px rgba(12, 24, 32, .18);
}

.form-title {
  margin-bottom: 24px;
}

.form-title h1 {
  font-size: 24px;
  line-height: 1.2;
  margin: 0 0 6px;
}

.form-title p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.field {
  margin-bottom: 16px;
}

.field label {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.field input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-bg);
  color: var(--color-text);
  font-size: 15px;
  transition: border-color .2s, box-shadow .2s, background .2s;
}

.field input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, .24);
}

.field input::placeholder {
  color: var(--color-text-muted);
}

.options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 13px;
}

.options label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
}

.options input {
  accent-color: var(--color-primary);
}

.link-btn {
  border: none;
  background: transparent;
  color: var(--color-primary-light);
  font-size: 13px;
  font-weight: 700;
  padding: 0;
}

.link-btn:hover {
  color: var(--color-accent);
}

.error-msg {
  margin: 0 0 14px;
  color: var(--color-dislike);
  font-size: 12px;
  text-align: center;
}

.btn-submit {
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 13px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  color: var(--color-bg);
  font-size: 15px;
  font-weight: 900;
  letter-spacing: .5px;
  transition: transform .2s, box-shadow .2s, opacity .2s;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(56, 189, 248, .30);
}

.btn-submit:disabled {
  cursor: not-allowed;
  opacity: .65;
}

@media (max-width: 768px) {
  .login-page {
    align-items: flex-start;
    padding: 24px 12px;
  }

  .login-wrap {
    max-width: 400px;
    min-height: auto;
    grid-template-columns: 1fr;
  }

  .brand {
    padding: 32px 24px;
  }

  .brand-logo {
    font-size: 36px;
  }

  .brand-features {
    display: none;
  }

  .form-panel {
    padding: 32px 24px;
  }
}
</style>
