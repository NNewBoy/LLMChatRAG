<template>
  <div class="document-view">
    <!-- 顶部导航栏 -->
    <div class="app-header">
      <div class="header-left">
        <span class="app-title">文档管理 & 错题集</span>
      </div>
      <div class="header-nav">
        <el-radio-group v-model="currentMode" @change="switchMode">
          <el-radio-button label="chat">普通对话</el-radio-button>
          <el-radio-button label="rag">RAG 对话</el-radio-button>
          <el-radio-button label="documents">文档管理</el-radio-button>
        </el-radio-group>
      </div>
      <div class="header-right"></div>
    </div>

    <div class="document-body">
      <el-tabs v-model="activeTab" class="document-tabs">
        <!-- 文档管理 Tab -->
        <el-tab-pane label="文档管理" name="documents">
          <div class="tab-content">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>上传文档生成 RAG 数据</span>
                </div>
              </template>
              <DocumentUpload @uploaded="handleUpload" />
              <DocumentList
                :documents="docStore.documents"
                @delete="handleDeleteDocument"
              />
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 错题集 Tab -->
        <el-tab-pane label="错题集编辑" name="badcases">
          <div class="tab-content">
            <BadCaseEditor
              :bad-cases="docStore.badCases"
              @refresh="docStore.fetchBadCases"
              @delete="docStore.deleteBadCase"
              @update="handleUpdateBadCase"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useDocumentStore } from '../stores/document'
import DocumentUpload from '../components/document/DocumentUpload.vue'
import DocumentList from '../components/document/DocumentList.vue'
import BadCaseEditor from '../components/rag/BadCaseEditor.vue'

const router = useRouter()
const docStore = useDocumentStore()

const currentMode = ref('documents')
const activeTab = ref('documents')

onMounted(async () => {
  await docStore.fetchDocuments()
  await docStore.fetchBadCases()
})

function switchMode(mode) {
  if (mode === 'chat') {
    router.push('/chat')
  } else if (mode === 'rag') {
    router.push('/rag')
  }
}

async function handleUpload(file) {
  try {
    await docStore.uploadDocument(file)
    ElMessage.success('文档上传成功，正在处理...')
    // 开始轮询状态
    pollDocumentStatus(docStore.documents[0].id)
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '文档上传失败'
    ElMessage.error(msg)
  }
}

function pollDocumentStatus(docId) {
  const poll = async () => {
    const doc = await docStore.fetchDocumentStatus(docId)
    if (doc && (doc.status === 'completed' || doc.status === 'failed')) {
      if (doc.status === 'completed') {
        ElMessage.success(`文档处理完成，共 ${doc.chunk_count} 个分块`)
      } else {
        ElMessage.error('文档处理失败: ' + (doc.error_message || ''))
      }
      return
    }
    setTimeout(poll, 3000) // 3 秒轮询
  }
  setTimeout(poll, 2000) // 2 秒后开始
}

async function handleDeleteDocument(id) {
  await docStore.deleteDocument(id)
  ElMessage.success('文档已删除')
}

async function handleUpdateBadCase({ id, correct_answer, use_as_example }) {
  await docStore.updateBadCase(id, correct_answer, use_as_example)
  ElMessage.success('错题已更新')
}
</script>

<style scoped>
.document-view {
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

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.document-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.document-tabs {
  max-width: 1000px;
  margin: 0 auto;
}

.tab-content {
  min-height: 400px;
}

.card-header {
  font-weight: 600;
}

@media (max-width: 768px) {
  .document-body {
    padding: 12px;
  }
  .header-nav :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 13px;
  }
}
</style>
