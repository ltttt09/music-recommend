<template>
  <div id="app-root">
    <div class="music-accent" aria-hidden="true">
      <span class="note note-1">♪</span>
      <span class="note note-2">♫</span>
      <span class="note note-3">♬</span>
    </div>
    <Navbar v-if="!isAdminLayout" />
    <main :class="{ 'admin-main': isAdminLayout }">
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <div :key="route.fullPath">
            <KeepAlive v-if="route.meta.keepAlive">
              <component :is="Component" :key="route.name" />
            </KeepAlive>
            <component v-else :is="Component" :key="route.fullPath" />
          </div>
        </transition>
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
  position: relative;
  z-index: 1;
}
main.admin-main {
  min-height: 100vh;
  padding-bottom: 32px;
}

/* Page transition */
.page-enter-active {
  transition: opacity .28s ease, transform .28s ease;
}
.page-leave-active {
  transition: opacity .18s ease, transform .18s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(.98);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(.99);
}

/* Floating music notes */
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
.note {
  display: inline-block;
}
.note-1 { animation: floatNote 4s ease-in-out infinite; }
.note-2 { animation: floatNote 5s ease-in-out infinite .6s; }
.note-3 { animation: floatNote 6s ease-in-out infinite 1.2s; }

@keyframes floatNote {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-14px) rotate(6deg); }
}

@media (max-width: 760px) {
  .music-accent { display: none; }
}
</style>
