<template>
  <div class="rag-view">
    <!-- 顶部导航栏 -->
    <AppHeader :current-mode="currentMode" title="LLMChatRAG - RAG 对话">
      <template #left>
        <el-button class="menu-btn" :icon="Fold" text @click="sidebarVisible = true" />
      </template>
      <template #right>
        <el-button :icon="Setting" text @click="settingsVisible = true" title="配置" />
      </template>
    </AppHeader>

    <div class="rag-body">
      <!-- 侧边栏 -->
      <div class="sidebar-pc">
        <ChatSidebar
          mode="rag"
          :conversations="store.conversations"
          :current-id="store.currentConversationId"
          @new-chat="handleNewChat"
          @select="handleSelect"
          @delete="store.deleteConversation"
          @rename="handleRename"
        />
      </div>

      <el-drawer v-model="sidebarVisible" direction="ltr" size="280px" :show-close="false">
        <RAGChatSidebar
          :conversations="store.conversations"
          :current-id="store.currentConversationId"
          @new-chat="handleNewChat"
          @select="handleSelect"
          @delete="store.deleteConversation"
          @rename="handleRename"
        />
      </el-drawer>

      <!-- 对话区 -->
      <div class="rag-main">
        <!-- 消息列表 -->
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

        <!-- 输入区 -->
        <ChatInput
          mode="rag"
          :is-streaming="store.isStreaming"
          @send="handleSend"
          @stop="store.stopGeneration"
        />
      </div>
    </div>

    <!-- 配置弹窗 -->
    <SettingsDialog
      v-model="settingsVisible"
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Fold, Setting } from '@element-plus/icons-vue'
import { useRagStore } from '../stores/rag'
import { chatApi } from '../api/chat'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatMessageList from '../components/chat/ChatMessageList.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import SettingsDialog from '../components/common/SettingsDialog.vue'
import AppHeader from '../components/common/AppHeader.vue'

const store = useRagStore()
const route = useRoute()
const router = useRouter()

const sidebarVisible = ref(false)
const settingsVisible = ref(false)
const currentMode = ref('rag')
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

<style scoped>
.rag-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: relative;
  z-index: 1;
}

.rag-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar-pc {
  width: 280px;
  border-right: 1px solid var(--glass-border, rgba(255,255,255,0.1));
  background: var(--glass-bg, rgba(255,255,255,0.06));
  backdrop-filter: blur(var(--glass-blur, 20px));
  -webkit-backdrop-filter: blur(var(--glass-blur, 20px));
}

.rag-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.message-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px;
}

.messages {
  max-width: 900px;
  margin: 0 auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

@media (max-width: 768px) {
  .sidebar-pc {
    display: none;
  }
  .message-list-container {
    padding: 0 12px;
  }
}
</style>
