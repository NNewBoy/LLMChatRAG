import apiClient from './client'

export const documentApi = {
  // 上传文档
  upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 上传超时 2 分钟
    })
  },

  // 获取所有文档列表
  list() {
    return apiClient.get('/documents')
  },

  // 获取文档处理状态
  getStatus(documentId) {
    return apiClient.get(`/documents/${documentId}/status`)
  },

  // 删除文档
  delete(documentId) {
    return apiClient.delete(`/documents/${documentId}`)
  },

  // 获取错题集列表
  getBadCases(params = {}) {
    return apiClient.get('/bad-cases', { params })
  },

  // 更新错题
  updateBadCase(badCaseId, correctAnswer, useAsExample) {
    return apiClient.put(`/bad-cases/${badCaseId}`, {
      correct_answer: correctAnswer,
      use_as_example: useAsExample,
    })
  },

  // 删除错题
  deleteBadCase(badCaseId) {
    return apiClient.delete(`/bad-cases/${badCaseId}`)
  },
}
