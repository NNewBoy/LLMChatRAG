import { defineStore } from 'pinia'
import { ref } from 'vue'
import { documentApi } from '../api/document'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref([])
  const badCases = ref([])

  // 上传文档
  async function uploadDocument(file) {
    try {
      const res = await documentApi.upload(file)
      documents.value.unshift(res.data.document)
      return res.data.document
    } catch (e) {
      console.error('上传文档失败:', e)
      throw e
    }
  }

  // 获取所有文档列表
  async function fetchDocuments() {
    try {
      const res = await documentApi.list()
      documents.value = res.data.documents || []
    } catch (e) {
      console.error('获取文档列表失败:', e)
    }
  }

  // 获取文档处理状态
  async function fetchDocumentStatus(documentId) {
    try {
      const res = await documentApi.getStatus(documentId)
      const doc = res.data.document
      // 更新本地列表中的文档状态
      const idx = documents.value.findIndex(d => d.id === documentId)
      if (idx !== -1) {
        documents.value[idx] = { ...documents.value[idx], ...doc }
      }
      return doc
    } catch (e) {
      console.error('获取文档状态失败:', e)
    }
  }

  // 删除文档
  async function deleteDocument(id) {
    try {
      await documentApi.delete(id)
      documents.value = documents.value.filter(d => d.id !== id)
    } catch (e) {
      console.error('删除文档失败:', e)
    }
  }

  // 获取错题集列表
  async function fetchBadCases() {
    try {
      const res = await documentApi.getBadCases()
      badCases.value = res.data.bad_cases || []
    } catch (e) {
      console.error('获取错题集失败:', e)
    }
  }

  // 更新错题
  async function updateBadCase(id, correctAnswer, useAsExample) {
    try {
      const res = await documentApi.updateBadCase(id, correctAnswer, useAsExample)
      const idx = badCases.value.findIndex(b => b.id === id)
      if (idx !== -1) {
        badCases.value[idx] = { ...badCases.value[idx], ...res.data.bad_case }
      }
    } catch (e) {
      console.error('更新错题失败:', e)
    }
  }

  // 删除错题
  async function deleteBadCase(id) {
    try {
      await documentApi.deleteBadCase(id)
      badCases.value = badCases.value.filter(b => b.id !== id)
    } catch (e) {
      console.error('删除错题失败:', e)
    }
  }

  return {
    documents,
    badCases,
    uploadDocument,
    fetchDocuments,
    fetchDocumentStatus,
    deleteDocument,
    fetchBadCases,
    updateBadCase,
    deleteBadCase,
  }
})
