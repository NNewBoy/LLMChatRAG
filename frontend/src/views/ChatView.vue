<template>
  <div class="chat-view">
    <!-- 顶部导航栏 -->
    <div class="app-header">
      <div class="header-left">
        <el-button class="menu-btn" :icon="Fold" text @click="sidebarVisible = true" />
        <span class="app-title">LLMChatRAG</span>
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

    <div class="chat-body">
      <!-- 侧边栏 (PC 端固定，移动端抽屉) -->
      <div class="sidebar-pc">
        <ChatSidebar
          :conversations="store.conversations"
          :current-id="store.currentConversationId"
          @new-chat="handleNewChat"
          @select="handleSelect"
          @delete="store.deleteConversation"
        />
      </div>

      <el-drawer v-model="sidebarVisible" direction="ltr" size="280px" :show-close="false">
        <ChatSidebar
          :conversations="store.conversations"
          :current-id="store.currentConversationId"
          @new-chat="handleNewChat"
          @select="handleSelect"
          @delete="store.deleteConversation"
        />
      </el-drawer>

      <!-- 对话区 -->
      <div class="chat-main">
        <ChatMessageList
          :messages="store.messages"
          :is-streaming="store.isStreaming"
          @regenerate="handleRegenerate"
          @followup="handleFollowup"
          @delete="store.deleteMessage"
        />
        <ChatInput
          :model="store.selectedModel"
          :models="store.availableModels"
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
      :models="store.availableModels"
      :disabled="store.isStreaming"
      :show-intent="true"
      :intent="store.enableIntentRecognition"
      @update:model="store.setSelectedModel"
      @update:intent="store.setEnableIntentRecognition"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Fold, Setting } from '@element-plus/icons-vue'
import { useChatStore } from '../stores/chat'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatMessageList from '../components/chat/ChatMessageList.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import SettingsDialog from '../components/common/SettingsDialog.vue'

const router = useRouter()
const route = useRoute()
const store = useChatStore()

const sidebarVisible = ref(false)
const settingsVisible = ref(false)
const currentMode = ref('chat')

onMounted(async () => {
  await store.fetchModels()
  await store.fetchConversations()
  // 从路由参数恢复会话
  if (route.params.conversationId) {
    await store.fetchMessages(route.params.conversationId)
  }
})

function switchMode(mode) {
  if (mode === 'rag') {
    router.push('/rag')
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
  router.push(`/chat/${id}`)
  sidebarVisible.value = false
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

<style scoped>
.chat-view {
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

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar-pc {
  width: 280px;
  border-right: 1px solid #e4e7ed;
  background: #fafafa;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
}
</style>
