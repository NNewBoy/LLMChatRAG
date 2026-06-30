<template>
  <div id="app">
    <div class="app-background"></div>
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()

onMounted(() => {
  // 初始化主题：优先 URI 参数 ?theme=light|dark，其次 localStorage，默认 dark
  themeStore.init()
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
  background: var(--bg-base);
  z-index: 0;
  transition: background 0.3s ease;
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
  transition: background 0.3s ease;
}
</style>
