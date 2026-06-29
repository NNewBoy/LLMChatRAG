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
          <input
            v-if="editingId === conv.id"
            :ref="(el) => editInputEl = el"
            v-model="editTitle"
            class="edit-input"
            @click.stop
            @keyup.enter="confirmRename(conv.id)"
            @keyup.esc="cancelRename"
          />
          <span v-else class="conv-title">{{ conv.title || 'RAG 对话' }}</span>
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
              :icon="Edit"
              @click.stop="startRename(conv)"
            />
            <el-button
              class="action-btn"
              text
              size="small"
              :icon="Delete"
              @click.stop="$emit('delete', conv.id)"
            />
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Plus, Document, Delete, Edit, Check, Close } from '@element-plus/icons-vue'

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
  editTitle.value = conv.title || 'RAG 对话'
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

.edit-input {
  flex: 1;
  font-size: 14px;
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
