<template>
  <div class="rag-chat-input">
    <div class="input-area">
      <el-input
        v-model="textContent"
        type="textarea"
        :rows="2"
        :autosize="{ minRows: 1, maxRows: 6 }"
        placeholder="输入问题，基于上传文档进行问答 (Enter 发送, Shift+Enter 换行)"
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
          :disabled="!textContent.trim()"
          @click="handleSend"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Promotion, VideoPause } from '@element-plus/icons-vue'

const props = defineProps({
  isStreaming: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'stop'])

const textContent = ref('')

function handleSend() {
  if (props.isStreaming) return
  const content = textContent.value.trim()
  if (!content) return
  emit('send', content)
  textContent.value = ''
}
</script>

<style scoped>
.rag-chat-input {
  border-top: 1px solid #e4e7ed;
  padding: 12px 24px;
  background: #fff;
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
  .rag-chat-input {
    padding: 8px 12px;
  }
}
</style>
