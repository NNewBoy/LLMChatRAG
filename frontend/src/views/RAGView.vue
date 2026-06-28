<template>
  <div class="rag-view">
    <!-- 顶部导航栏 -->
    <div class="app-header">
      <div class="header-left">
        <el-button class="menu-btn" :icon="Fold" text @click="sidebarVisible = true" />
        <span class="app-title">LLMChatRAG - RAG 对话</span>
      </div>
      <div class="header-nav">
        <el-radio-group v-model="currentMode" @change="switchMode">
          <el-radio-button label="chat">普通对话</el-radio-button>
          <el-radio-button label="rag">RAG 对话</el-radio-button>
          <el-radio-button label="documents">文档管理</el-radio-button>
        </el-radio-group>
      </div>
      <div class="header-right">
        <el-button :icon="Setting" text @click="settingsVisible = true" title="配置" />
      </div>
    </div>

    <div class="rag-body">
      <!-- 侧边栏 -->
      <div class="sidebar-pc">
        <RAGChatSidebar
          :conversations="store.conversations"
          :current-id="store.currentConversationId"
          @new-chat="handleNewChat"
          @select="handleSelect"
          @delete="store.deleteConversation"
        />
      </div>

      <el-drawer v-model="sidebarVisible" direction="ltr" size="280px" :show-close="false">
        <RAGChatSidebar
          :conversations="store.conversations"
          :current-id="store.currentConversationId"
          @new-chat="handleNewChat"
          @select="handleSelect"
          @delete="store.deleteConversation"
        />
      </el-drawer>

      <!-- 对话区 -->
      <div class="rag-main">
        <!-- 消息列表 -->
        <div class="message-list-container">
          <div v-if="store.messages.length === 0" class="empty-state">
            <el-empty description="开始 RAG 对话，基于上传文档进行问答" />
          </div>
          <div v-else class="messages">
            <template v-for="(msg, index) in store.messages" :key="msg.id || index">
              <RAGChatMessage
                :message="msg"
                :is-streaming="store.isStreaming && index === store.messages.length - 1"
                @regenerate="handleRegenerate"
                @followup="handleFollowup"
                @delete="store.deleteMessage"
                @feedback="handleFeedback"
              />
            </template>
          </div>
        </div>

        <!-- 输入区 -->
        <RAGChatInput
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
import { useRouter } from 'vue-router'
import { Fold, Setting } from '@element-plus/icons-vue'
import { useRagStore } from '../stores/rag'
import { chatApi } from '../api/chat'
import RAGChatSidebar from '../components/rag/RAGChatSidebar.vue'
import RAGChatMessage from '../components/rag/RAGChatMessage.vue'
import RAGChatInput from '../components/rag/RAGChatInput.vue'
import SettingsDialog from '../components/common/SettingsDialog.vue'

const router = useRouter()
const store = useRagStore()

const sidebarVisible = ref(false)
const settingsVisible = ref(false)
const currentMode = ref('rag')
const llmModels = ref([])

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
})

function switchMode(mode) {
  if (mode === 'chat') {
    router.push('/chat')
  } else if (mode === 'documents') {
    router.push('/documents')
  }
}

async function handleNewChat() {
  await store.createConversation()
  sidebarVisible.value = false
}

async function handleSelect(id) {
  await store.fetchMessages(id)
  sidebarVisible.value = false
}

function handleSend(content) {
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
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.menu-btn {
  display: none;
}

.rag-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar-pc {
  width: 280px;
  border-right: 1px solid #e4e7ed;
  background: #fafafa;
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
  .menu-btn {
    display: inline-flex;
  }
  .sidebar-pc {
    display: none;
  }
  .header-nav :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 13px;
  }
  .message-list-container {
    padding: 0 12px;
  }
}
</style>
