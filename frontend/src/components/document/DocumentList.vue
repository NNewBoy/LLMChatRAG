<template>
  <div class="document-list">
    <el-table v-if="documents.length > 0" :data="documents" style="width: 100%">
      <el-table-column prop="filename" label="文件名" min-width="200" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <DocumentStatus :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="chunk_count" label="分块数" width="80" />
      <el-table-column prop="file_type" label="类型" width="80" />
      <el-table-column label="大小" width="100">
        <template #default="{ row }">
          {{ formatSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button
            text
            size="small"
            type="danger"
            :icon="Delete"
            @click="$emit('delete', row.id)"
          />
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="暂无文档，请上传文档生成 RAG 数据" />
  </div>
</template>

<script setup>
import { Delete } from '@element-plus/icons-vue'
import DocumentStatus from './DocumentStatus.vue'

defineProps({
  documents: { type: Array, default: () => [] },
})

defineEmits(['delete'])

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.document-list {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .document-list :deep(.el-table) {
    font-size: 12px;
  }
}
</style>
