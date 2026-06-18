import { reactive } from 'vue'
import api from './api.js'

// Shared reactive auth state so Navbar updates immediately after login/register
export const auth = reactive({
  loggedIn: !!localStorage.getItem('token'),
  username: localStorage.getItem('username') || '',
  userId: Number(localStorage.getItem('user_id')) || 0,

  login(token, userId, username) {
    localStorage.setItem('token', token)
    localStorage.setItem('user_id', String(userId))
    localStorage.setItem('username', username)
    this.loggedIn = true
    this.username = username
    this.userId = userId
  },

  logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
    this.loggedIn = false
    this.username = ''
    this.userId = 0
  },

  async validate() {
    if (!localStorage.getItem('token')) return false
    try {
      const data = await api.me()
      const user = data.user || {}
      this.loggedIn = true
      this.username = user.username || localStorage.getItem('username') || ''
      this.userId = Number(user.id) || Number(localStorage.getItem('user_id')) || 0
      localStorage.setItem('username', this.username)
      localStorage.setItem('user_id', String(this.userId))
      return true
    } catch {
      this.logout()
      return false
    }
  }
})

window.addEventListener('auth-expired', () => auth.logout())
