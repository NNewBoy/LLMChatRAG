<template>
  <div class="rag-chat-message">
    <ChatMessage
      :message="message"
      :is-streaming="isStreaming"
      @regenerate="$emit('regenerate', $event)"
      @followup="$emit('followup', $event)"
      @delete="$emit('delete', $event)"
    />
    <!-- 反馈标记 (仅助手消息且非流式时显示) -->
    <div class="feedback-area" v-if="message.role === 'assistant' && !isStreaming && message.id && !message.id.startsWith('temp')">
      <FeedbackBadge
        :value="message.is_correct"
        @feedback="(val) => $emit('feedback', { id: message.id, isCorrect: val })"
      />
    </div>
  </div>
</template>

<script setup>
import ChatMessage from '../chat/ChatMessage.vue'
import FeedbackBadge from './FeedbackBadge.vue'

defineProps({
  message: { type: Object, required: true },
  isStreaming: { type: Boolean, default: false },
})

defineEmits(['regenerate', 'followup', 'delete', 'feedback'])
</script>

<style scoped>
.rag-chat-message {
  position: relative;
}

.feedback-area {
  margin-left: 44px;
  padding-bottom: 8px;
}
</style>
