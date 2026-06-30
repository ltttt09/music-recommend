import { createRouter, createWebHashHistory } from 'vue-router'
import Home from './pages/Home.vue'
import Browse from './pages/Browse.vue'
import TrackDetail from './pages/TrackDetail.vue'
import Recommend from './pages/Recommend.vue'
import History from './pages/History.vue'
import Playlist from './pages/Playlist.vue'
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Admin from './pages/Admin.vue'
import AdminTrackDetail from './pages/AdminTrackDetail.vue'
import Insights from './pages/Insights.vue'
import Favorites from './pages/Favorites.vue'
import Profile from './pages/Profile.vue'
import My from './pages/My.vue'
import NowPlaying from './pages/NowPlaying.vue'

const keepAlive = { keepAlive: true }
const requireAuth = { requireAuth: true }
const detailPage = { scrollTop: true }

const routes = [
  { path: '/', name: 'Home', component: Home, meta: keepAlive },
  { path: '/browse', name: 'Browse', component: Browse, meta: keepAlive },
  { path: '/insights', name: 'Insights', component: Insights, meta: { ...keepAlive, ...requireAuth } },
  { path: '/favorites', name: 'Favorites', component: Favorites, meta: { ...keepAlive, ...requireAuth } },
  { path: '/profile', name: 'Profile', component: Profile, meta: { ...keepAlive, ...requireAuth } },
  { path: '/my', name: 'My', component: My, meta: { ...keepAlive, ...requireAuth } },
  { path: '/track/:id', name: 'TrackDetail', component: TrackDetail, props: true, meta: detailPage },
  { path: '/playing/:id', name: 'NowPlaying', component: NowPlaying, props: true, meta: detailPage },
  { path: '/recommend', name: 'Recommend', component: Recommend, meta: { ...keepAlive, ...requireAuth } },
  { path: '/history', name: 'History', component: History, meta: { ...keepAlive, ...requireAuth } },
  { path: '/onboarding', redirect: '/recommend' },
  { path: '/playlist/:id', name: 'Playlist', component: Playlist, props: true, meta: detailPage },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/admin', name: 'Admin', component: Admin, meta: { adminLayout: true, scrollTop: true, keepAlive: true } },
  { path: '/admin/track/:id', name: 'AdminTrackDetail', component: AdminTrackDetail, props: true, meta: { adminLayout: true, scrollTop: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    // 跳转到新页面时从头显示（需求7）
    return { top: 0 }
  },
})

// 路由守卫：未登录用户跳转到登录页（Bug4）
router.beforeEach((to, from, next) => {
  if (to.meta?.requireAuth && !localStorage.getItem('token')) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
