<template>
  <div id="app-root">
    <div class="music-accent" aria-hidden="true">
      <span>♪</span>
      <span>♫</span>
      <span>♬</span>
    </div>
    <Navbar />
    <main>
      <router-view />
    </main>
    <AudioPlayer />
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
import AudioPlayer from './components/AudioPlayer.vue'
</script>

<style scoped>
main {
  min-height: calc(100vh - 56px);
  padding-bottom: 80px;
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
