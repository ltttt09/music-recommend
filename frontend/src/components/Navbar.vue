<template>
  <nav class="navbar">
    <div class="navbar-inner container">
      <router-link to="/" class="logo">🎵 SoundMind</router-link>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/browse">曲库</router-link>
        <router-link to="/recommend">发现</router-link>
        <router-link to="/my">我的</router-link>
      </div>
      <div class="nav-right">
        <template v-if="auth.loggedIn">
          <router-link to="/my" class="user-tag">{{ auth.username }}</router-link>
          <button class="btn-ghost-sm" @click="doLogout">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="auth-link">登录</router-link>
          <router-link to="/register" class="auth-link">注册</router-link>
        </template>
        <button class="theme-btn" @click="toggleTheme" :title="isDark ? '浅色模式' : '深色模式'">
          {{ isDark ? '☀' : '☾' }}
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../auth.js'

const router = useRouter()
const isDark = ref(true)

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

function doLogout() {
  auth.logout()
  router.push('/')
}

onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved === 'light') { isDark.value = false; document.documentElement.setAttribute('data-theme', 'light') }
})
</script>

<style scoped>
.navbar {
  background: rgba(26, 29, 39, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  position: sticky; top: 0; z-index: 100;
}
[data-theme="light"] .navbar {
  background: rgba(255, 255, 255, 0.85);
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.navbar-inner { display: flex; align-items: center; justify-content: space-between; height: 56px; }
.logo {
  font-size: 20px; font-weight: 800;
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; letter-spacing: 1px;
}
.nav-links { display: flex; gap: 4px; }
.nav-links a {
  color: var(--color-text-muted); font-size: 14px; font-weight: 500;
  transition: all 0.2s; padding: 6px 14px; border-radius: 8px;
}
.nav-links a:hover { color: var(--color-text); background: var(--color-surface-hover); }
.nav-links a.router-link-active { color: var(--color-primary-light); background: rgba(108,92,231,0.1); }
.nav-right { display: flex; align-items: center; gap: 8px; }
.user-tag { font-size: 13px; color: var(--color-accent); text-decoration: none; padding: 4px 8px; border-radius: 6px; }
.user-tag:hover { background: var(--color-surface-hover); }
.auth-link { font-size: 13px; color: var(--color-text-muted); padding: 4px 10px; border-radius: 6px; transition: all .2s; }
.auth-link:hover { color: var(--color-text); background: var(--color-surface-hover); }
.btn-ghost-sm {
  background: none; border: 1px solid var(--color-border); color: var(--color-text-muted);
  padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all .2s;
}
.btn-ghost-sm:hover { border-color: var(--color-dislike); color: var(--color-dislike); }
.theme-btn {
  background: none; border: 1px solid var(--color-border); border-radius: 50%;
  width: 34px; height: 34px; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  color: var(--color-text); cursor: pointer; transition: all .2s;
}
.theme-btn:hover { border-color: var(--color-primary); }
@media (max-width: 768px) {
  .nav-links { gap: 0; }
  .nav-links a { font-size: 12px; padding: 6px 8px; }
  .logo { font-size: 17px; }
}
</style>
