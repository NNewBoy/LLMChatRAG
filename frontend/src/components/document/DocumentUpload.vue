<template>
  <div class="document-upload">
    <el-upload
      ref="uploadRef"
      drag
      :auto-upload="true"
      :show-file-list="false"
      :http-request="customUpload"
      accept=".pdf,.docx,.doc,.html,.htm,.txt,.md"
      :before-upload="beforeUpload"
    >
      <div class="drag-area">
        <el-icon class="drag-icon"><Upload /></el-icon>
        <div class="drag-text">
          {{ uploading ? '上传中...' : '将文件拖拽到此处，或点击上传' }}
        </div>
        <div class="upload-tip">支持 PDF、Word、HTML、TXT 格式，单个文件不超过 10MB</div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['uploaded'])

const uploadRef = ref()
const uploading = ref(false)

function beforeUpload(file) {
  const maxSize = 10 * 1024 * 1024 // 1MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

async function customUpload(options) {
  uploading.value = true
  try {
    emit('uploaded', options.file)
  } catch (e) {
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.document-upload {
  margin-bottom: 16px;
}

.drag-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.drag-icon {
  font-size: 40px;
  color: var(--accent-primary, #6366f1);
  margin-bottom: 12px;
}

.drag-text {
  font-size: 15px;
  color: var(--text-secondary, #cbd5e1);
  margin-bottom: 4px;
}

.upload-tip {
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
}

/* 覆盖 el-upload 拖拽区深色主题 */
:deep(.el-upload-dragger) {
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-glass);
  transition: background 220ms cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 220ms cubic-bezier(0.16, 1, 0.3, 1), transform 220ms cubic-bezier(0.16, 1, 0.3, 1);
  padding: 0;
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--accent-primary, #6366f1);
  background: var(--glass-bg-hover);
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: var(--accent-primary, #6366f1);
  background: var(--glass-bg-hover);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .drag-area {
    padding: 16px 12px;
  }

  .drag-icon {
    font-size: 32px;
    margin-bottom: 8px;
  }

  .drag-text {
    font-size: 14px;
  }
}
</style>
