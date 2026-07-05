<template>
  <AppLayout v-model:sidebar="sidebarVisible" current-mode="rag" title="LLMChatRAG - RAG 对话">
    <template #sidebar>
      <ChatSidebar
        mode="rag"
        :conversations="store.conversations"
        :current-id="store.currentConversationId"
        @new-chat="handleNewChat"
        @select="handleSelect"
        @delete="store.deleteConversation"
        @rename="handleRename"
      />
    </template>

    <ChatMessageList
      ref="messageListRef"
      :messages="store.messages"
      :is-streaming="store.isStreaming"
      :show-feedback="true"
      empty-text="开始 RAG 对话，基于上传文档进行问答"
      @regenerate="handleRegenerate"
      @followup="handleFollowup"
      @delete="store.deleteMessage"
      @feedback="handleFeedback"
    />

    <template #footer>
      <ChatInput
        mode="rag"
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
        :models="llmModels"
        :disabled="store.isStreaming"
        :show-rag="true"
        :embedding-model="store.selectedEmbeddingModel"
        :embedding-models="store.availableEmbeddingModels"
        :query-rewriting="store.enableQueryRewriting"
        :hybrid-search="store.enableHybridSearch"
        :reranking="store.enableReranking"
        @update:model="store.setSelectedModel"
        @update:embeddingModel="store.setSelectedEmbeddingModel"
        @update:queryRewriting="store.setEnableQueryRewriting"
        @update:hybridSearch="store.setEnableHybridSearch"
        @update:reranking="store.setEnableReranking"
      />
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRagStore } from '../stores/rag'
import { chatApi } from '../api/chat'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatMessageList from '../components/chat/ChatMessageList.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import SettingsDialog from '../components/common/SettingsDialog.vue'
import AppLayout from '../components/common/AppLayout.vue'

const store = useRagStore()
const route = useRoute()
const router = useRouter()

const sidebarVisible = ref(false)
const llmModels = ref([])
const messageListRef = ref(null)

onMounted(async () => {
  await store.fetchModels()
  await store.fetchEmbeddingModels()
  await store.fetchConversations()
  // 获取 LLM 模型列表
  try {
    const res = await chatApi.getModels()
    llmModels.value = res.data.models || []
  } catch (e) {
    console.error('获取模型列表失败:', e)
  }
  // 从路由参数恢复会话
  if (route.params.conversationId) {
    await store.fetchMessages(route.params.conversationId)
  }
})

async function handleNewChat() {
  const conv = await store.createConversation()
  router.push(`/rag/${conv.id}`)
  sidebarVisible.value = false
}

async function handleSelect(id) {
  await store.fetchMessages(id)
  router.push(`/rag/${id}`)
  sidebarVisible.value = false
}

function handleRename({ id, title }) {
  store.renameConversation(id, title)
}

function handleSend({ content, image }) {
  store.sendMessage(content, null)
}

function handleRegenerate(messageId) {
  store.regenerateMessage(messageId)
}

function handleFollowup(messageId) {
  const msg = store.messages.find(m => m.id === messageId)
  if (msg) {
    const content = window.prompt('请输入追问内容:')
    if (content) {
      store.sendMessage(content, messageId)
    }
  }
}

function handleFeedback({ id, isCorrect }) {
  store.submitFeedback(id, isCorrect)
}
</script>
