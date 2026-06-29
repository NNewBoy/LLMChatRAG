<template>
  <div class="chat-sidebar">
    <el-button type="primary" class="new-chat-btn" @click="$emit('new-chat')">
      <el-icon><Plus /></el-icon>
      {{ mode === 'rag' ? '新建 RAG 对话' : '新建对话' }}
    </el-button>
    <el-scrollbar>
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: conv.id === currentId }"
          @click="$emit('select', conv.id)"
        >
          <el-icon><component :is="mode === 'rag' ? Document : ChatDotRound" /></el-icon>
          <input
            v-if="editingId === conv.id"
            :ref="(el) => editInputEl = el"
            v-model="editTitle"
            class="edit-input"
            @click.stop
            @keyup.enter="confirmRename(conv.id)"
            @keyup.esc="cancelRename"
          />
          <span v-else class="conv-title">{{ conv.title || defaultTitle }}</span>
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
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { Plus, ChatDotRound, Document, Delete, Edit, Check, Close } from '@element-plus/icons-vue'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
  mode: { type: String, default: 'chat' }, // 'chat' | 'rag'
})

const emit = defineEmits(['new-chat', 'select', 'delete', 'rename'])

const defaultTitle = computed(() => props.mode === 'rag' ? 'RAG 对话' : '新对话')

const editingId = ref(null)
const editTitle = ref('')
const editInputEl = ref(null)

function startRename(conv) {
  editingId.value = conv.id
  editTitle.value = conv.title || defaultTitle.value
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
  background: transparent;
}

.new-chat-btn {
  width: 100%;
  margin-bottom: 12px;
}

.conversation-list {
  padding: 0 4px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-sm, 8px);
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  color: var(--text-secondary, #cbd5e1);
}

.conversation-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.conversation-item.active {
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-primary-light, #818cf8);
}

.conv-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-input {
  flex: 1;
  font-size: 14px;
  border: 1px solid var(--accent-primary, #6366f1);
  border-radius: var(--radius-sm, 8px);
  padding: 2px 6px;
  outline: none;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary, #f8fafc);
}

.item-actions {
  display: flex;
  gap: 2px;
}

.action-btn {
  opacity: 0;
  transition: opacity 0.2s;
  color: var(--text-muted, #94a3b8);
}

.conversation-item:hover .action-btn {
  opacity: 1;
}
</style>
