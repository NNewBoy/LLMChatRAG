import apiClient, { streamChat } from './client'

export const ragApi = {
  // 获取可用 Embedding 模型列表
  getEmbeddingModels() {
    return apiClient.get('/embedding-models')
  },

  // 获取 RAG 历史会话列表
  getConversations() {
    return apiClient.get('/rag/conversations')
  },

  // 创建 RAG 新会话
  createConversation(title) {
    return apiClient.post('/rag/conversations', { mode: 'rag', title })
  },

  // 删除 RAG 会话
  deleteConversation(id) {
    return apiClient.delete(`/rag/conversations/${id}`)
  },

  // 获取会话消息历史
  getMessages(conversationId) {
    return apiClient.get(`/rag/conversations/${conversationId}/messages`)
  },

  // 发送 RAG 消息 (SSE 流式)
  sendMessageStream(conversationId, body, callbacks) {
    return streamChat(`/rag/conversations/${conversationId}/messages`, body, callbacks)
  },

  // 停止生成
  stopGeneration(conversationId, messageId) {
    return apiClient.post(`/rag/conversations/${conversationId}/messages/${messageId}/stop`)
  },

  // 重新生成 (SSE 流式)
  regenerateMessageStream(conversationId, messageId, body, callbacks) {
    return streamChat(`/rag/conversations/${conversationId}/messages/${messageId}/regenerate`, body, callbacks)
  },

  // 删除消息
  deleteMessage(conversationId, messageId) {
    return apiClient.delete(`/rag/conversations/${conversationId}/messages/${messageId}`)
  },

  // 标记答案正确/错误
  submitFeedback(conversationId, messageId, isCorrect) {
    return apiClient.post(`/rag/conversations/${conversationId}/messages/${messageId}/feedback`, {
      is_correct: isCorrect,
    })
  },
}
