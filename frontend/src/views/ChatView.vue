<template>
  <AppLayout v-model:sidebar="sidebarVisible" current-mode="chat" title="LLMChatRAG">
    <template #sidebar>
      <ChatSidebar
        :conversations="store.conversations"
        :current-id="store.currentConversationId"
        @new-chat="handleNewChat"
        @select="handleSelect"
        @delete="store.deleteConversation"
        @rename="handleRename"
      />
    </template>

    <ChatMessageList
      :messages="store.messages"
      :is-streaming="store.isStreaming"
      @regenerate="handleRegenerate"
      @followup="handleFollowup"
      @delete="store.deleteMessage"
    />

    <template #footer>
      <ChatInput
        :model="store.selectedModel"
        :models="store.availableModels"
        :is-streaming="store.isStreaming"
        @send="handleSend"
        @stop="store.stopGeneration"
      />
    </template>

    <template #settings="{ visible, setVisible }">
      <SettingsDialog
        :model-value="visible"
        @update:model-value="setVisible"
        :model="store.selectedModel"
        :models="store.availableModels"
        :disabled="store.isStreaming"
        :show-intent="true"
        :intent="store.enableIntentRecognition"
        @update:model="store.setSelectedModel"
        @update:intent="store.setEnableIntentRecognition"
      />
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChatStore } from '../stores/chat'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatMessageList from '../components/chat/ChatMessageList.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import SettingsDialog from '../components/common/SettingsDialog.vue'
import AppLayout from '../components/common/AppLayout.vue'

const router = useRouter()
const route = useRoute()
const store = useChatStore()

const sidebarVisible = ref(false)

onMounted(async () => {
  await store.fetchModels()
  await store.fetchConversations()
  // 从路由参数恢复会话
  if (route.params.conversationId) {
    await store.fetchMessages(route.params.conversationId)
  }
})

async function handleNewChat() {
  const conv = await store.createConversation()
  router.push(`/chat/${conv.id}`)
  sidebarVisible.value = false
}

async function handleSelect(id) {
  await store.fetchMessages(id)
  router.push(`/chat/${id}`)
  sidebarVisible.value = false
}

function handleRename({ id, title }) {
  store.renameConversation(id, title)
}

function handleSend({ content, image }) {
  store.sendMessage(content, image, null)
}

function handleRegenerate(messageId) {
  store.regenerateMessage(messageId)
}

function handleFollowup(messageId) {
  // 追问：以该消息为基础发起新对话
  const msg = store.messages.find(m => m.id === messageId)
  if (msg) {
    // 这里简单实现：弹出输入框让用户输入追问内容
    // 实际可将 parent_message_id 设为 messageId
    const content = window.prompt('请输入追问内容:')
    if (content) {
      store.sendMessage(content, null, messageId)
    }
  }
}
</script>
