<template>
  <el-dialog v-model="visible" title="配置" :width="dialogWidth" :close-on-click-modal="true" append-to-body>
    <div class="settings-content">
      <!-- 主题切换 (所有页面通用) -->
      <div class="config-section">
        <label class="config-label">外观主题</label>
        <div class="theme-switch-row">
          <div class="theme-option" :class="{ active: themeStore.theme === 'light' }" @click="setTheme('light')">
            <el-icon :size="18"><Sunny /></el-icon>
            <span>浅色</span>
          </div>
          <div class="theme-option" :class="{ active: themeStore.theme === 'dark' }" @click="setTheme('dark')">
            <el-icon :size="18"><Moon /></el-icon>
            <span>深色</span>
          </div>
        </div>
      </div>

      <!-- LLM 模型选择 -->
      <div class="config-section" v-if="showIntent || showRag">
        <label class="config-label">LLM 模型</label>
        <el-select
          v-model="localModel"
          style="width: 100%"
          :disabled="disabled"
          @change="emit('update:model', $event)"
        >
          <el-option
            v-for="m in models"
            :key="m.id"
            :label="m.name + (m.multimodal ? ' (多模态)' : '')"
            :value="m.id"
          >
            <span>{{ m.name }}</span>
            <el-tag v-if="m.multimodal" size="small" type="success" style="margin-left: 8px">多模态</el-tag>
          </el-option>
        </el-select>
      </div>

      <!-- 意图识别 (仅 Chat) -->
      <div class="config-section" v-if="showIntent">
        <div class="toggle-row">
          <div>
            <span>意图识别</span>
            <p class="toggle-hint">开启后 Agent 自动识别意图，涉及知识库的问题调用 RAG 工具</p>
          </div>
          <el-switch v-model="localIntent" @change="emit('update:intent', $event)" />
        </div>
      </div>

      <!-- RAG 配置 (仅 RAG) -->
      <template v-if="showRag">
        <div class="config-section">
          <label class="config-label">Embedding 模型</label>
          <el-select
            v-model="localEmbeddingModel"
            style="width: 100%"
            @change="emit('update:embeddingModel', $event)"
          >
            <el-option
              v-for="m in embeddingModels"
              :key="m.id"
              :label="m.name"
              :value="m.id"
            />
          </el-select>
        </div>

        <div class="config-section">
          <div class="toggle-row">
            <span>Query 改写</span>
            <el-switch v-model="localQueryRewriting" @change="emit('update:queryRewriting', $event)" />
          </div>
        </div>

        <div class="config-section">
          <div class="toggle-row">
            <span>混合检索 (BM25+向量)</span>
            <el-switch v-model="localHybridSearch" @change="emit('update:hybridSearch', $event)" />
          </div>
        </div>

        <div class="config-section">
          <div class="toggle-row">
            <span>重排序</span>
            <el-switch v-model="localReranking" @change="emit('update:reranking', $event)" />
          </div>
        </div>
      </template>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { Sunny, Moon } from '@element-plus/icons-vue'
import { useThemeStore } from '../../stores/theme'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  model: { type: String, default: '' },
  models: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  showIntent: { type: Boolean, default: false },
  intent: { type: Boolean, default: true },
  showRag: { type: Boolean, default: false },
  embeddingModel: { type: String, default: '' },
  embeddingModels: { type: Array, default: () => [] },
  queryRewriting: { type: Boolean, default: true },
  hybridSearch: { type: Boolean, default: false },
  reranking: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:modelValue',
  'update:model',
  'update:intent',
  'update:embeddingModel',
  'update:queryRewriting',
  'update:hybridSearch',
  'update:reranking',
])

const themeStore = useThemeStore()

const visible = ref(props.modelValue)
const localModel = ref(props.model)
const localIntent = ref(props.intent)
const localEmbeddingModel = ref(props.embeddingModel)
const localQueryRewriting = ref(props.queryRewriting)
const localHybridSearch = ref(props.hybridSearch)
const localReranking = ref(props.reranking)

// 响应式弹窗宽度
const windowWidth = ref(window.innerWidth)
const dialogWidth = computed(() => {
  return windowWidth.value < 768 ? '92%' : '480px'
})

function updateWidth() {
  windowWidth.value = window.innerWidth
}

onMounted(() => window.addEventListener('resize', updateWidth))
onUnmounted(() => window.removeEventListener('resize', updateWidth))

// 切换主题（直接刷新 CSS，无需重启页面）
function setTheme(theme) {
  themeStore.setTheme(theme)
}

watch(() => props.modelValue, (val) => { visible.value = val })
watch(visible, (val) => { emit('update:modelValue', val) })

watch(() => props.model, (val) => { localModel.value = val })
watch(() => props.intent, (val) => { localIntent.value = val })
watch(() => props.embeddingModel, (val) => { localEmbeddingModel.value = val })
watch(() => props.queryRewriting, (val) => { localQueryRewriting.value = val })
watch(() => props.hybridSearch, (val) => { localHybridSearch.value = val })
watch(() => props.reranking, (val) => { localReranking.value = val })
</script>

<style scoped>
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #f8fafc);
}

.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--text-secondary, #cbd5e1);
}

.toggle-hint {
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
  margin: 4px 0 0;
  max-width: 320px;
}

/* 主题切换按钮组 */
.theme-switch-row {
  display: flex;
  gap: 12px;
}

.theme-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: var(--radius-md, 12px);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: var(--glass-bg, rgba(255, 255, 255, 0.06));
  color: var(--text-secondary, #cbd5e1);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.theme-option:hover {
  background: var(--glass-bg-hover, rgba(255, 255, 255, 0.1));
  border-color: var(--glass-border-hover, rgba(255, 255, 255, 0.2));
}

.theme-option.active {
  background: var(--accent-primary, #6366f1);
  border-color: var(--accent-primary, #6366f1);
  color: #fff;
  box-shadow: 0 0 12px var(--accent-primary-glow, rgba(99, 102, 241, 0.3));
}
</style>
