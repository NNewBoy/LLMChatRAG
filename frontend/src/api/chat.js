import apiClient, { streamChat } from './client'

export const chatApi = {
  // 获取可用 LLM 模型列表
  getModels() {
    return apiClient.get('/models')
  },

  // 获取历史会话列表
  getConversations() {
    return apiClient.get('/chat/conversations')
  },

  // 创建新会话
  createConversation(title) {
    return apiClient.post('/chat/conversations', { mode: 'chat', title })
  },

  // 删除会话
  deleteConversation(id) {
    return apiClient.delete(`/chat/conversations/${id}`)
  },

  // 重命名会话
  renameConversation(id, title) {
    return apiClient.put(`/chat/conversations/${id}`, { title })
  },

  // 获取会话消息历史
  getMessages(conversationId) {
    return apiClient.get(`/chat/conversations/${conversationId}/messages`)
  },

  // 发送消息 (SSE 流式)
  sendMessageStream(conversationId, body, callbacks) {
    return streamChat(`/chat/conversations/${conversationId}/messages`, body, callbacks)
  },

  // 停止生成
  stopGeneration(conversationId, messageId) {
    return apiClient.post(`/chat/conversations/${conversationId}/messages/${messageId}/stop`)
  },

  // 重新生成 (SSE 流式)
  regenerateMessageStream(conversationId, messageId, body, callbacks) {
    return streamChat(`/chat/conversations/${conversationId}/messages/${messageId}/regenerate`, body, callbacks)
  },

  // 删除消息
  deleteMessage(conversationId, messageId) {
    return apiClient.delete(`/chat/conversations/${conversationId}/messages/${messageId}`)
  },
}
