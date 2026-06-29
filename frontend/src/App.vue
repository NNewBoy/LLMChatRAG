<template>
  <div id="app" class="dark">
    <div class="app-background"></div>
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  document.documentElement.classList.add('dark')
})
</script>

<style>
#app {
  height: 100vh;
  width: 100%;
  position: relative;
  z-index: 1;
}

.app-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-base, #0a0a0f);
  z-index: 0;
}

.app-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gradient-hero);
  pointer-events: none;
}
</style>
