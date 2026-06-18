<template>
  <div id="app-root">
    <div class="music-accent" aria-hidden="true">
      <span>♪</span>
      <span>♫</span>
      <span>♬</span>
    </div>
    <Navbar v-if="!isAdminLayout" />
    <main :class="{ 'admin-main': isAdminLayout }">
      <router-view v-slot="{ Component, route }">
        <KeepAlive>
          <component :is="Component" v-if="route.meta.keepAlive" :key="route.name" />
        </KeepAlive>
        <component :is="Component" v-if="!route.meta.keepAlive" :key="route.fullPath" />
      </router-view>
    </main>
    <AudioPlayer v-if="!isAdminLayout" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'
import AudioPlayer from './components/AudioPlayer.vue'

const route = useRoute()
const isAdminLayout = computed(() => Boolean(route.meta?.adminLayout))
</script>

<style scoped>
main {
  min-height: calc(100vh - 56px);
  padding-bottom: 80px;
}
main.admin-main {
  min-height: 100vh;
  padding-bottom: 32px;
}
.music-accent {
  position: fixed;
  inset: 76px 24px auto auto;
  display: flex;
  gap: 18px;
  color: var(--color-primary-light);
  opacity: .14;
  font-size: 48px;
  font-weight: 800;
  pointer-events: none;
  z-index: 0;
}
main {
  position: relative;
  z-index: 1;
}
@media (max-width: 760px) {
  .music-accent { display: none; }
}
</style>
