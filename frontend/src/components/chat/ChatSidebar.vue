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
        <input
          v-if="editingId === conv.id"
          :ref="(el) => editInputEl = el"
          v-model="editTitle"
          class="edit-input"
          @click.stop
          @keyup.enter="confirmRename(conv.id)"
          @keyup.esc="cancelRename"
        />
        <span v-else class="conv-title">{{ conv.title || '新对话' }}</span>
        <div class="item-actions" v-if="editingId === conv.id">
          <el-button text size="small" @click.stop="confirmRename(conv.id)">
            <el-icon><Check /></el-icon>
          </el-button>
          <el-button text size="small" @click.stop="cancelRename">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div class="item-actions" v-else>
          <el-button
            class="action-btn"
            text
            size="small"
            @click.stop="startRename(conv)"
          >
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button
            class="action-btn"
            text
            size="small"
            @click.stop="$emit('delete', conv.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
      <el-empty v-if="conversations.length === 0" description="暂无历史会话" :image-size="60" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Plus, ChatDotRound, Delete, Edit, Check, Close } from '@element-plus/icons-vue'

defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
})

const emit = defineEmits(['new-chat', 'select', 'delete', 'rename'])

const editingId = ref(null)
const editTitle = ref('')
const editInputEl = ref(null)

function startRename(conv) {
  editingId.value = conv.id
  editTitle.value = conv.title || '新对话'
  nextTick(() => {
    editInputEl.value?.focus()
    editInputEl.value?.select()
  })
}

function cancelRename() {
  editingId.value = null
  editTitle.value = ''
}

function confirmRename(id) {
  const title = editTitle.value.trim()
  if (title) {
    emit('rename', { id, title })
  }
  cancelRename()
}
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

.edit-input {
  flex: 1;
  font-size: 13px;
  border: 1px solid #409eff;
  border-radius: 4px;
  padding: 2px 6px;
  outline: none;
  background: #fff;
}

.item-actions {
  display: flex;
  gap: 2px;
}

.action-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .action-btn {
  opacity: 1;
}
</style>
