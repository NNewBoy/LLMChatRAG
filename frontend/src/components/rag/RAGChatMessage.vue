<template>
  <div class="rag-chat-message">
    <ChatMessage
      :message="message"
      :is-streaming="isStreaming"
      :show-feedback="true"
      @regenerate="$emit('regenerate', $event)"
      @followup="$emit('followup', $event)"
      @delete="$emit('delete', $event)"
      @feedback="$emit('feedback', $event)"
    />
  </div>
</template>

<script setup>
import ChatMessage from '../chat/ChatMessage.vue'

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
</style>
