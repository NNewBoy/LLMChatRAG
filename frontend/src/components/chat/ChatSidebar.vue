<template>
  <div class="chat-sidebar">
    <el-button type="primary" class="new-chat-btn" @click="$emit('new-chat')">
      <el-icon><Plus /></el-icon>
      新建对话
    </el-button>
    <div class="conversation-list">
      <div
        v-for="conv in conversations"
        :key="conv.id"
        class="conversation-item"
        :class="{ active: conv.id === currentId }"
        @click="$emit('select', conv.id)"
      >
        <el-icon><ChatDotRound /></el-icon>
        <span class="conv-title">{{ conv.title || '新对话' }}</span>
        <el-button
          class="delete-btn"
          text
          size="small"
          @click.stop="$emit('delete', conv.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
      <el-empty v-if="conversations.length === 0" description="暂无历史会话" :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { Plus, ChatDotRound, Delete } from '@element-plus/icons-vue'

defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
})

defineEmits(['new-chat', 'select', 'delete'])
</script>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
}

.new-chat-btn {
  width: 100%;
  margin-bottom: 12px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
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
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .delete-btn {
  opacity: 1;
}
</style>
