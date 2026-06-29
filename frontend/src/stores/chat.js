import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '../api/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConversationId = ref(null)
  const messages = ref([])
  const isStreaming = ref(false)
  const selectedModel = ref('glm-5.2')
  const availableModels = ref([])
  const enableIntentRecognition = ref(false)

  // 获取可用 LLM 模型列表
  async function fetchModels() {
    try {
      const res = await chatApi.getModels()
      availableModels.value = res.data.models || []
    } catch (e) {
      console.error('获取模型列表失败:', e)
    }
  }

  // 获取历史会话列表
  async function fetchConversations() {
    try {
      const res = await chatApi.getConversations()
      conversations.value = res.data.conversations || []
    } catch (e) {
      console.error('获取会话列表失败:', e)
    }
  }

  // 创建新会话
  async function createConversation(title = '新对话') {
    try {
      const res = await chatApi.createConversation(title)
      const conv = res.data.conversation
      conversations.value.unshift(conv)
      currentConversationId.value = conv.id
      messages.value = []
      return conv
    } catch (e) {
      console.error('创建会话失败:', e)
    }
  }

  // 删除会话
  async function deleteConversation(id) {
    try {
      await chatApi.deleteConversation(id)
      conversations.value = conversations.value.filter(c => c.id !== id)
      if (currentConversationId.value === id) {
        currentConversationId.value = null
        messages.value = []
      }
    } catch (e) {
      console.error('删除会话失败:', e)
    }
  }

  // 重命名会话
  async function renameConversation(id, title) {
    try {
      await chatApi.renameConversation(id, title)
      const conv = conversations.value.find(c => c.id === id)
      if (conv) conv.title = title
    } catch (e) {
      console.error('重命名会话失败:', e)
      throw e
    }
  }

  // 获取会话消息历史
  async function fetchMessages(conversationId) {
    try {
      const res = await chatApi.getMessages(conversationId)
      messages.value = res.data.messages || []
      currentConversationId.value = conversationId
    } catch (e) {
      console.error('获取消息历史失败:', e)
    }
  }

  // 发送消息 (SSE 流式)
  async function sendMessage(content, image = null, parentMessageId = null, callbacks = {}) {
    if (!currentConversationId.value) {
      await createConversation()
    }

    const convId = currentConversationId.value
    isStreaming.value = true

    // 添加用户消息到列表
    const userMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content,
      thinking: null,
      tool_calls: null,
      is_correct: null,
      parent_message_id: parentMessageId,
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMsg)

    // 添加助手消息占位
    const assistantMsg = {
      id: 'temp-assistant-' + Date.now(),
      role: 'assistant',
      content: '',
      thinking: '',
      tool_calls: '',
      is_correct: null,
      parent_message_id: userMsg.id,
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)
    // 获取响应式代理对象，后续修改才能触发 UI 更新
    const reactiveAssistantMsg = messages.value[messages.value.length - 1]

    try {
      await chatApi.sendMessageStream(
        convId,
        {
          content,
          model: selectedModel.value,
          image,
          parent_message_id: parentMessageId,
          enable_intent_recognition: enableIntentRecognition.value,
        },
        {
          onInit: (data) => {
            // 更新临时 ID 为真实 message_id，用于停止操作
            reactiveAssistantMsg.id = data.message_id
          },
          onThinking: (data) => {
            reactiveAssistantMsg.thinking += (reactiveAssistantMsg.thinking ? '\n' : '') + data.content
            callbacks.onThinking?.(data)
          },
          onIntent: (data) => {
            reactiveAssistantMsg.thinking += `\n[意图识别: ${data.intent}, 置信度: ${data.confidence}]`
            callbacks.onIntent?.(data)
          },
          onToolCall: (data) => {
            reactiveAssistantMsg.tool_calls += `\n[工具调用: ${data.tool_name}]`
            callbacks.onToolCall?.(data)
          },
          onToolResult: (data) => {
            reactiveAssistantMsg.tool_calls += `\n[工具结果: ${data.tool_output}]`
            callbacks.onToolResult?.(data)
          },
          onToken: (data) => {
            reactiveAssistantMsg.content += data.content
            callbacks.onToken?.(data)
          },
          onDone: (data) => {
            reactiveAssistantMsg.id = data.message_id
            isStreaming.value = false
            // 刷新会话列表（后端在第一条消息时会自动生成标题）
            fetchConversations()
            callbacks.onDone?.(data)
          },
          onError: (data) => {
            reactiveAssistantMsg.content += `\n[错误: ${data.message}]`
            isStreaming.value = false
            callbacks.onError?.(data)
          },
        }
      )
    } catch (e) {
      isStreaming.value = false
      reactiveAssistantMsg.content += `\n[请求失败: ${e.message}]`
    }
  }

  // 停止生成
  async function stopGeneration() {
    if (!currentConversationId.value) return
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      try {
        await chatApi.stopGeneration(currentConversationId.value, lastMsg.id)
      } catch (e) {
        console.error('停止生成失败:', e)
      }
    }
    isStreaming.value = false
  }

  // 删除消息
  async function deleteMessage(messageId) {
    try {
      await chatApi.deleteMessage(currentConversationId.value, messageId)
      // 查找被删除的消息，若是助手回答则同时删除对应的用户提问
      const msg = messages.value.find(m => m.id === messageId)
      const parentId = msg?.parent_message_id
      messages.value = messages.value.filter(m => m.id !== messageId && m.id !== parentId)
    } catch (e) {
      console.error('删除消息失败:', e)
    }
  }

  // 重新生成
  async function regenerateMessage(messageId, callbacks = {}) {
    isStreaming.value = true
    // 找到消息位置，移除该消息及之后的所有消息
    const idx = messages.value.findIndex(m => m.id === messageId)
    if (idx === -1) return

    const removedMsg = messages.value[idx]
    const parentMsgId = removedMsg.parent_message_id

    // 移除该消息及之后的所有消息
    messages.value = messages.value.slice(0, idx)

    // 添加新的助手消息占位
    const assistantMsg = {
      id: 'temp-regen-' + Date.now(),
      role: 'assistant',
      content: '',
      thinking: '',
      tool_calls: '',
      is_correct: null,
      parent_message_id: parentMsgId,
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)
    const reactiveMsg = messages.value[messages.value.length - 1]

    try {
      await chatApi.regenerateMessageStream(
        currentConversationId.value,
        messageId,
        { model: selectedModel.value },
        {
          onThinking: (data) => {
            reactiveMsg.thinking += (reactiveMsg.thinking ? '\n' : '') + data.content
          },
          onToken: (data) => {
            reactiveMsg.content += data.content
          },
          onDone: (data) => {
            reactiveMsg.id = data.message_id
            isStreaming.value = false
          },
          onError: (data) => {
            reactiveMsg.content += `\n[错误: ${data.message}]`
            isStreaming.value = false
          },
        }
      )
    } catch (e) {
      isStreaming.value = false
      reactiveMsg.content += `\n[请求失败: ${e.message}]`
    }
  }

  function setSelectedModel(modelId) {
    selectedModel.value = modelId
  }

  function setEnableIntentRecognition(enabled) {
    enableIntentRecognition.value = enabled
  }

  return {
    conversations,
    currentConversationId,
    messages,
    isStreaming,
    selectedModel,
    availableModels,
    enableIntentRecognition,
    fetchModels,
    fetchConversations,
    createConversation,
    deleteConversation,
    renameConversation,
    fetchMessages,
    sendMessage,
    stopGeneration,
    deleteMessage,
    regenerateMessage,
    setSelectedModel,
    setEnableIntentRecognition,
  }
})
