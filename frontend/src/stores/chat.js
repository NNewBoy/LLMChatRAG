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
  const enableIntentRecognition = ref(true)

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
          onThinking: (data) => {
            assistantMsg.thinking += (assistantMsg.thinking ? '\n' : '') + data.content
            callbacks.onThinking?.(data)
          },
          onIntent: (data) => {
            assistantMsg.thinking += `\n[意图识别: ${data.intent}, 置信度: ${data.confidence}]`
            callbacks.onIntent?.(data)
          },
          onToolCall: (data) => {
            assistantMsg.tool_calls += `\n[工具调用: ${data.tool_name}]`
            callbacks.onToolCall?.(data)
          },
          onToolResult: (data) => {
            assistantMsg.tool_calls += `\n[工具结果: ${data.tool_output}]`
            callbacks.onToolResult?.(data)
          },
          onToken: (data) => {
            assistantMsg.content += data.content
            callbacks.onToken?.(data)
          },
          onDone: (data) => {
            assistantMsg.id = data.message_id
            isStreaming.value = false
            callbacks.onDone?.(data)
          },
          onError: (data) => {
            assistantMsg.content += `\n[错误: ${data.message}]`
            isStreaming.value = false
            callbacks.onError?.(data)
          },
        }
      )
    } catch (e) {
      isStreaming.value = false
      assistantMsg.content += `\n[请求失败: ${e.message}]`
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
      messages.value = messages.value.filter(m => m.id !== messageId)
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

    try {
      await chatApi.regenerateMessageStream(
        currentConversationId.value,
        messageId,
        { model: selectedModel.value },
        {
          onThinking: (data) => {
            assistantMsg.thinking += (assistantMsg.thinking ? '\n' : '') + data.content
          },
          onToken: (data) => {
            assistantMsg.content += data.content
          },
          onDone: (data) => {
            assistantMsg.id = data.message_id
            isStreaming.value = false
          },
          onError: (data) => {
            assistantMsg.content += `\n[错误: ${data.message}]`
            isStreaming.value = false
          },
        }
      )
    } catch (e) {
      isStreaming.value = false
      assistantMsg.content += `\n[请求失败: ${e.message}]`
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
    fetchMessages,
    sendMessage,
    stopGeneration,
    deleteMessage,
    regenerateMessage,
    setSelectedModel,
    setEnableIntentRecognition,
  }
})
