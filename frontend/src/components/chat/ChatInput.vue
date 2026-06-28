<template>
  <div class="chat-input">
    <!-- 工具栏 -->
    <div class="input-toolbar">
      <ImageUpload
        v-if="supportsMultimodal"
        v-model="imageData"
        :disabled="isStreaming"
        @change="onImageChange"
      />
    </div>
    <!-- 输入区 -->
    <div class="input-area">
      <el-input
        v-model="textContent"
        type="textarea"
        :rows="2"
        :autosize="{ minRows: 1, maxRows: 6 }"
        placeholder="输入消息，按 Enter 发送，Shift+Enter 换行"
        :disabled="isStreaming"
        resize="none"
        @keydown.enter.exact.prevent="handleSend"
      />
      <div class="send-button">
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
</template>

<script setup>
import { ref, computed } from 'vue'
import { Promotion, VideoPause } from '@element-plus/icons-vue'
import ImageUpload from './ImageUpload.vue'

const props = defineProps({
  model: { type: String, default: '' },
  models: { type: Array, default: () => [] },
  isStreaming: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'stop'])

const textContent = ref('')
const imageData = ref(null)

// 检查当前模型是否支持多模态
const supportsMultimodal = computed(() => {
  const model = props.models.find(m => m.id === props.model)
  return model?.multimodal || false
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
  border-top: 1px solid #e4e7ed;
  padding: 12px 24px;
  background: #fff;
}

.input-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.input-area {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.send-button {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .chat-input {
    padding: 8px 12px;
  }
  .input-toolbar {
    gap: 8px;
  }
}
</style>
