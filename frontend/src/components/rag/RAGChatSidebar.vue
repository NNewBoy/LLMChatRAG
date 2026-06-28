<template>
  <div class="rag-chat-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" :icon="Plus" @click="$emit('new-chat')" style="width: 100%">
        新建 RAG 对话
      </el-button>
    </div>
    <el-scrollbar>
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: conv.id === currentId }"
          @click="$emit('select', conv.id)"
        >
          <el-icon><Document /></el-icon>
          <span class="conv-title">{{ conv.title || 'RAG 对话' }}</span>
          <el-button
            class="delete-btn"
            text
            size="small"
            :icon="Delete"
            @click.stop="$emit('delete', conv.id)"
          />
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { Plus, Document, Delete } from '@element-plus/icons-vue'

defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
})

defineEmits(['new-chat', 'select', 'delete'])
</script>

<style scoped>
.rag-chat-sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
}

.conversation-list {
  padding: 0 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .delete-btn {
  opacity: 1;
}
</style>
