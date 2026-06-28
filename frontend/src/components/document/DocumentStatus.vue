<template>
  <span class="document-status">
    <el-tag :type="tagType" size="small" effect="light">
      <el-icon v-if="isLoading" class="is-loading"><Loading /></el-icon>
      {{ statusText }}
    </el-tag>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps({
  status: { type: String, default: 'uploading' },
})

const STATUS_MAP = {
  uploading: { text: '上传中', type: 'info' },
  parsing: { text: '解析中', type: 'warning' },
  chunking: { text: '分块中', type: 'warning' },
  embedding: { text: '向量化中', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  failed: { text: '失败', type: 'danger' },
}

const tagType = computed(() => STATUS_MAP[props.status]?.type || 'info')
const statusText = computed(() => STATUS_MAP[props.status]?.text || props.status)
const isLoading = computed(() => ['uploading', 'parsing', 'chunking', 'embedding'].includes(props.status))
</script>

<style scoped>
.document-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.is-loading {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
