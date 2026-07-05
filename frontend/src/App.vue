<template>
  <div id="app">
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
</style>
