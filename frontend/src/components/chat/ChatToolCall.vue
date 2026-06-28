<template>
  <div class="chat-tool-call" v-if="content">
    <el-collapse>
      <el-collapse-item name="tools">
        <template #title>
          <div class="tool-header">
            <el-icon><Tools /></el-icon>
            <span>工具调用</span>
          </div>
        </template>
        <div class="tool-content">{{ content }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { Tools } from '@element-plus/icons-vue'

defineProps({
  content: { type: String, default: '' },
})
</script>

<style scoped>
.chat-tool-call {
  margin: 8px 0;
  background: #ecf5ff;
  border-radius: 8px;
  padding: 0 12px;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #409eff;
}

.tool-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  padding: 8px 0;
}
</style>
