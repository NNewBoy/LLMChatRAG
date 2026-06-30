import { defineStore } from 'pinia'

const STORAGE_KEY = 'llmchatrag-theme'
const VALID_THEMES = ['dark', 'light']

function getStoredTheme() {
  try {
    const t = localStorage.getItem(STORAGE_KEY)
    if (t && VALID_THEMES.includes(t)) return t
  } catch (e) {
    // localStorage 不可用时忽略
  }
  return 'light' // 默认浅色
}

function applyTheme(theme) {
  const html = document.documentElement
  if (theme === 'dark') {
    html.classList.add('dark')
  } else {
    html.classList.remove('dark')
  }
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: getStoredTheme(),
  }),

  getters: {
    isDark: (state) => state.theme === 'dark',
  },

  actions: {
    /**
     * 初始化主题：
     * 1. 优先读取 URI 参数 ?theme=light|dark（便于外部平台跳转指定主题）
     * 2. 其次读取 localStorage 持久化值
     * 3. 默认 dark
     */
    init() {
      // 检查 URI 参数
      const params = new URLSearchParams(window.location.search)
      const uriTheme = params.get('theme')
      if (uriTheme && VALID_THEMES.includes(uriTheme)) {
        this.setTheme(uriTheme)
        return
      }
      applyTheme(this.theme)
    },

    setTheme(theme) {
      if (!VALID_THEMES.includes(theme)) return
      this.theme = theme
      applyTheme(theme)
      try {
        localStorage.setItem(STORAGE_KEY, theme)
      } catch (e) {
        // 忽略写入失败
      }
    },

    toggleTheme() {
      this.setTheme(this.theme === 'dark' ? 'light' : 'dark')
    },
  },
})
