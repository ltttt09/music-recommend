import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { auth } from './auth.js'
import './style.css'

auth.validate()

createApp(App).use(router).mount('#app')
