import { createRouter, createWebHashHistory } from 'vue-router'
import Home from './pages/Home.vue'
import Browse from './pages/Browse.vue'
import TrackDetail from './pages/TrackDetail.vue'
import Recommend from './pages/Recommend.vue'
import History from './pages/History.vue'
import Onboarding from './pages/Onboarding.vue'
import Playlist from './pages/Playlist.vue'
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Admin from './pages/Admin.vue'
import Insights from './pages/Insights.vue'
import Favorites from './pages/Favorites.vue'
import Profile from './pages/Profile.vue'
import My from './pages/My.vue'
import NowPlaying from './pages/NowPlaying.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/browse', name: 'Browse', component: Browse },
  { path: '/insights', name: 'Insights', component: Insights },
  { path: '/favorites', name: 'Favorites', component: Favorites },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/my', name: 'My', component: My },
  { path: '/track/:id', name: 'TrackDetail', component: TrackDetail, props: true },
  { path: '/playing/:id', name: 'NowPlaying', component: NowPlaying, props: true },
  { path: '/recommend', name: 'Recommend', component: Recommend },
  { path: '/history', name: 'History', component: History },
  { path: '/onboarding', name: 'Onboarding', component: Onboarding },
  { path: '/playlist/:id', name: 'Playlist', component: Playlist, props: true },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/admin', name: 'Admin', component: Admin },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
