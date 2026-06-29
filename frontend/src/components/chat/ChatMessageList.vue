<template>
  <div class="chat-message-list" ref="containerRef">
    <div v-if="messages.length === 0" class="empty-state">
      <el-empty description="开始一段新对话" />
    </div>
    <template v-else>
      <ChatMessage
        v-for="(msg, index) in messages"
        :key="msg.id || index"
        :message="msg"
        :is-streaming="isStreaming && index === messages.length - 1"
        @regenerate="$emit('regenerate', $event)"
        @followup="$emit('followup', $event)"
        @delete="$emit('delete', $event)"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  isStreaming: { type: Boolean, default: false },
})

defineEmits(['regenerate', 'followup', 'delete'])

const containerRef = ref(null)

// 自动滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
}

// 消息数量变化时滚动
watch(() => props.messages.length, scrollToBottom)
// 流式输出期间，最后一条消息内容变化时也滚动
watch(
  () => props.messages[props.messages.length - 1]?.content,
  scrollToBottom
)
watch(
  () => props.messages[props.messages.length - 1]?.thinking,
  scrollToBottom
)
// 流式结束后操作按钮出现，需要滚动露出
watch(() => props.isStreaming, (val) => {
  if (!val) scrollToBottom()
})
</script>

<style scoped>
.chat-message-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
