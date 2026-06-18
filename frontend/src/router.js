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
const detailPage = { scrollTop: true }

const routes = [
  { path: '/', name: 'Home', component: Home, meta: keepAlive },
  { path: '/browse', name: 'Browse', component: Browse, meta: keepAlive },
  { path: '/insights', name: 'Insights', component: Insights, meta: keepAlive },
  { path: '/favorites', name: 'Favorites', component: Favorites, meta: keepAlive },
  { path: '/profile', name: 'Profile', component: Profile, meta: keepAlive },
  { path: '/my', name: 'My', component: My, meta: keepAlive },
  { path: '/track/:id', name: 'TrackDetail', component: TrackDetail, props: true },
  { path: '/playing/:id', name: 'NowPlaying', component: NowPlaying, props: true },
  { path: '/recommend', name: 'Recommend', component: Recommend, meta: keepAlive },
  { path: '/history', name: 'History', component: History, meta: keepAlive },
  { path: '/onboarding', redirect: '/recommend' },
  { path: '/playlist/:id', name: 'Playlist', component: Playlist, props: true, meta: detailPage },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/admin', name: 'Admin', component: Admin, meta: { adminLayout: true, scrollTop: true, keepAlive: true } },
  { path: '/admin/track/:id', name: 'AdminTrackDetail', component: AdminTrackDetail, props: true, meta: { adminLayout: true, scrollTop: true } },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.meta?.scrollTop || to.name === 'TrackDetail' || to.name === 'NowPlaying') return { top: 0 }
    return false
  },
})
