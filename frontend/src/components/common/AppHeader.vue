<template>
  <div class="app-header glass">
    <div class="header-left">
      <slot name="left" />
      <span class="app-title">{{ title }}</span>
    </div>
    <nav class="header-nav" aria-label="主导航">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        :class="{ active: isActive(item.path) }"
        @click="emit('switch-mode', item.value)"
      >
        <el-icon :size="18"><component :is="item.icon" /></el-icon>
        <span class="nav-label">{{ item.label }}</span>
        <span class="nav-label--short">{{ item.shortLabel }}</span>
      </router-link>
    </nav>
    <div class="header-right">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ChatDotRound, Collection, Folder } from '@element-plus/icons-vue'

defineProps({
  currentMode: { type: String, required: true },
  title: { type: String, default: '' },
})

const emit = defineEmits(['switch-mode'])

const router = useRouter()
const route = useRoute()

const menuItems = [
  { value: 'chat', path: '/chat', label: '普通对话', shortLabel: '对话', icon: ChatDotRound },
  { value: 'rag', path: '/rag', label: 'RAG 对话', shortLabel: 'RAG', icon: Collection },
  { value: 'documents', path: '/documents', label: '文档管理', shortLabel: '文档', icon: Folder },
]

function isActive(path) {
  return route.path.startsWith(path)
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 58px;
  z-index: 10;
}

.header-nav {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 4px;
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  transition: color 150ms cubic-bezier(0.16, 1, 0.3, 1), background 150ms cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
}

.nav-link:hover {
  color: var(--accent-primary-light);
}

.nav-link.active {
  color: var(--accent-primary-light);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 2px;
  height: 2px;
  border-radius: 2px;
  background: var(--accent-primary-light);
}

.nav-label--short {
  display: none;
}

.header-left {
  flex: 0 0 240px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  flex: 0 0 240px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  background: linear-gradient(135deg, var(--accent-primary-light), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.menu-btn) {
  display: none;
}

/* 平板适配 */
@media (max-width: 1024px) {
  .header-left {
    flex: 0 0 160px;
  }
  .header-right {
    flex: 0 0 160px;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header-left,
  .header-right {
    flex: 1 1 0;
  }

  .app-title {
    display: none;
  }

  :deep(.menu-btn) {
    display: inline-flex;
  }

  .header-nav {
    flex: 0 0 auto;
    gap: 2px;
  }

  .nav-link {
    padding: 8px 12px;
    font-size: 13px;
  }

  .nav-label {
    display: none;
  }

  .nav-label--short {
    display: inline;
  }

  .nav-link.active::after {
    left: 8px;
    right: 8px;
  }
}

/* 小屏手机适配 */
@media (max-width: 480px) {
  .app-header {
    height: 44px;
    padding: 0 16px;
  }

  .nav-link {
    padding: 6px 10px;
    font-size: 12px;
  }
}
</style>
