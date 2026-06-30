<template>
  <div class="document-view">
    <!-- 顶部导航栏 -->
    <AppHeader :current-mode="currentMode" title="文档管理 & 错题集">
      <template #right>
        <el-button :icon="Setting" text @click="settingsVisible = true" title="配置" />
      </template>
    </AppHeader>

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

    <!-- 配置弹窗（主题切换） -->
    <SettingsDialog v-model="settingsVisible" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import { useDocumentStore } from '../stores/document'
import DocumentUpload from '../components/document/DocumentUpload.vue'
import DocumentList from '../components/document/DocumentList.vue'
import BadCaseEditor from '../components/rag/BadCaseEditor.vue'
import AppHeader from '../components/common/AppHeader.vue'
import SettingsDialog from '../components/common/SettingsDialog.vue'

const docStore = useDocumentStore()

const currentMode = ref('documents')
const activeTab = ref('documents')
const settingsVisible = ref(false)

onMounted(async () => {
  await docStore.fetchDocuments()
  await docStore.fetchBadCases()
})

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

.document-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-main);
  position: relative;
  z-index: 1;
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
}
</style>
