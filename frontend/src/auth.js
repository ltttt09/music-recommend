import { reactive } from 'vue'

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
  }
})
