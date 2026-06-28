<template>
  <div class="document-upload">
    <el-upload
      ref="uploadRef"
      :auto-upload="true"
      :show-file-list="false"
      :http-request="customUpload"
      accept=".pdf,.docx,.doc,.html,.htm,.txt,.md"
      :before-upload="beforeUpload"
    >
      <el-button type="primary" :icon="Upload" :loading="uploading">
        {{ uploading ? '上传中...' : '上传文档' }}
      </el-button>
      <template #tip>
        <div class="upload-tip">支持 PDF、Word、HTML、TXT 格式，单个文件不超过 50MB</div>
      </template>
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
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB')
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

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>
