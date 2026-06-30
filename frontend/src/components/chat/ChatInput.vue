<template>
  <div class="chat-input">
    <div class="input-bubble">
      <!-- 上层：输入区 -->
      <div class="input-area">
        <el-input
          v-model="textContent"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 12 }"
          :placeholder="placeholder"
          :disabled="isStreaming"
          resize="none"
          class="chat-textarea"
          @keydown.enter.exact.prevent="handleSend"
        />
      </div>

      <!-- 下层：工具栏 -->
      <div class="input-toolbar">
        <div class="toolbar-right">
          <ImageUpload
            v-if="mode === 'chat' && supportsMultimodal"
            v-model="imageData"
            :disabled="isStreaming"
            @change="onImageChange"
          />
          <el-button
            v-if="isStreaming"
            type="danger"
            circle
            @click="$emit('stop')"
          >
            <el-icon><VideoPause /></el-icon>
          </el-button>
          <el-button
            v-else
            type="primary"
            circle
            :disabled="!textContent.trim() && !imageData"
            @click="handleSend"
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Promotion, VideoPause } from '@element-plus/icons-vue'
import ImageUpload from './ImageUpload.vue'

const props = defineProps({
  model: { type: String, default: '' },
  models: { type: Array, default: () => [] },
  isStreaming: { type: Boolean, default: false },
  mode: { type: String, default: 'chat' }, // 'chat' | 'rag'
})

const emit = defineEmits(['send', 'stop'])

const textContent = ref('')
const imageData = ref(null)

// 检查当前模型是否支持多模态
const supportsMultimodal = computed(() => {
  const model = props.models.find(m => m.id === props.model)
  return model?.multimodal || false
})

const placeholder = computed(() => {
  const isMobile = window.innerWidth < 768
  const hint = isMobile ? '' : ' (Enter 发送, Shift+Enter 换行)'
  return props.mode === 'rag'
    ? `输入问题，基于上传文档进行问答${hint}`
    : `输入消息${hint}`
})

function onImageChange(data) {
  imageData.value = data
}

function handleSend() {
  if (props.isStreaming) return
  const content = textContent.value.trim()
  if (!content && !imageData.value) return

  emit('send', {
    content,
    image: imageData.value,
  })

  // 清空输入
  textContent.value = ''
  imageData.value = null
}
</script>

<style scoped>
.chat-input {
  padding: 12px 24px;
  max-width: 100%;
}

/* 气泡框 */
.input-bubble {
  background: var(--glass-bg, rgba(255, 255, 255, 0.06));
  backdrop-filter: blur(var(--glass-blur, 20px));
  -webkit-backdrop-filter: blur(var(--glass-blur, 20px));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 16px);
  padding: 8px 12px 4px;
  max-width: 800px;
  margin: 0 auto;
  transition: border-color 0.2s, box-shadow 0.2s;
}

/* 浅色模式：白色背景 + 阴影 */
html:not(.dark) .input-bubble {
  background: #ffffff;
  border: 1px solid var(--glass-border);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
}

html:not(.dark) .input-bubble:focus-within {
  border-color: var(--accent-primary);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08), 0 0 0 3px var(--accent-primary-glow);
}

.input-bubble:focus-within {
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* 上层输入区 */
.input-area {
  max-height: 40vh;
  overflow-y: auto;
}

.input-area :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  box-shadow: none;
  color: var(--text-primary, #f8fafc);
  font-size: 15px;
  line-height: 1.6;
  padding: 6px 4px;
  resize: none;
}

.input-area :deep(.el-textarea__inner)::placeholder {
  color: var(--text-muted, #94a3b8);
}

/* 下层工具栏 */
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 4px 0 2px;
  min-height: 36px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-input {
    padding: 8px 12px;
  }

  .input-bubble {
    border-radius: var(--radius-md, 12px);
    padding: 6px 10px 4px;
  }

  .input-area :deep(.el-textarea__inner) {
    font-size: 14px;
  }
}

/* 尊重减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .input-bubble {
    transition: none;
  }
}
</style>
