<template>
  <div class="chat-sidebar">
    <el-button type="primary" class="new-chat-btn" @click="$emit('new-chat')">
      <el-icon><Plus /></el-icon>
      {{ mode === 'rag' ? '新建 RAG 对话' : '新建对话' }}
    </el-button>
    <el-scrollbar ref="scrollbarRef" @scroll="handleScroll">
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
            @blur="handleBlur(conv)"
          />
          <span v-else class="conv-title">{{ conv.title || defaultTitle }}</span>
          <!-- 更多操作下拉菜单（非编辑状态） -->
          <el-dropdown
            v-if="editingId !== conv.id"
            trigger="click"
            placement="bottom-end"
            @click.stop
            @command="handleCommand($event, conv)"
          >
            <el-button class="action-btn" text size="small" @click.stop>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">
                  <el-icon><Edit /></el-icon> 重命名
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon> 删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <el-empty v-if="conversations.length === 0" description="暂无历史会话" :image-size="60" />
      </div>
    </el-scrollbar>
    <!-- 底部渐隐遮罩：内容可滚动时显示 -->
    <div v-if="showScrollFade" class="scroll-fade-bottom"></div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, watch } from 'vue'
import { Plus, ChatDotRound, Document, Delete, Edit, MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
  mode: { type: String, default: 'chat' }, // 'chat' | 'rag'
})

const emit = defineEmits(['new-chat', 'select', 'delete', 'rename'])

const defaultTitle = computed(() => props.mode === 'rag' ? 'RAG 对话' : '新对话')

const editingId = ref(null)
const editTitle = ref('')
const originalTitle = ref('')
const editInputEl = ref(null)
const scrollbarRef = ref(null)
const showScrollFade = ref(false)

// 检查是否可滚动且未到底部
function updateScrollFade() {
  const wrapRef = scrollbarRef.value?.wrapRef
  if (!wrapRef) return
  const maxScroll = wrapRef.scrollHeight - wrapRef.clientHeight
  if (maxScroll <= 0) {
    showScrollFade.value = false
    return
  }
  showScrollFade.value = wrapRef.scrollTop < maxScroll - 20
}

// 监听滚动
function handleScroll({ scrollTop }) {
  const wrapRef = scrollbarRef.value?.wrapRef
  if (!wrapRef) return
  const maxScroll = wrapRef.scrollHeight - wrapRef.clientHeight
  showScrollFade.value = scrollTop < maxScroll - 20
}

// 初始化 + 会话列表变化时检查
onMounted(updateScrollFade)
watch(() => props.conversations, () => nextTick(updateScrollFade), { deep: true })

function startRename(conv) {
  editingId.value = conv.id
  editTitle.value = conv.title || defaultTitle.value
  originalTitle.value = editTitle.value
  nextTick(() => {
    editInputEl.value?.focus()
    editInputEl.value?.select()
  })
}

function cancelRename() {
  editingId.value = null
  editTitle.value = ''
  originalTitle.value = ''
}

function confirmRename(id) {
  const title = editTitle.value.trim()
  if (title) {
    emit('rename', { id, title })
  }
  cancelRename()
}

// 失焦时判断名称是否变更
function handleBlur(conv) {
  const title = editTitle.value.trim()
  if (title && title !== originalTitle.value) {
    emit('rename', { id: conv.id, title })
  }
  cancelRename()
}

// 下拉菜单命令
function handleCommand(command, conv) {
  if (command === 'rename') {
    startRename(conv)
  } else if (command === 'delete') {
    emit('delete', conv.id)
  }
}
</script>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px 0;
  background: transparent;
  position: relative;
}

.new-chat-btn {
  width: calc(100% - 24px);
  margin: 0 12px 12px;
}

/* scrollbar 内缩，滚动条不贴边 */
.chat-sidebar :deep(.el-scrollbar__bar.is-vertical) {
  right: 2px;
}

.conversation-list {
  padding: 0 12px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  min-height: 44px;
  border-radius: var(--radius-sm, 8px);
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  color: var(--text-secondary, #cbd5e1);
}

.conversation-item:hover {
  background: var(--el-fill-color, rgba(255, 255, 255, 0.06));
}

.conversation-item.active {
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent-primary, #6366f1);
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
  min-width: 0;
  height: 20px;
  font-size: 14px;
  border: 1px solid var(--accent-primary, #6366f1);
  border-radius: var(--radius-sm, 8px);
  padding: 0 6px;
  outline: none;
  background: var(--el-fill-color, rgba(255, 255, 255, 0.05));
  color: var(--text-primary, #f8fafc);
}

.action-btn {
  visibility: hidden;
  transition: visibility 0.2s;
  color: var(--text-muted, #94a3b8);
  flex-shrink: 0;
}

.conversation-item:hover .action-btn,
.conversation-item.active .action-btn {
  visibility: visible;
}

/* 移动端：恒定显示（无 hover） */
@media (hover: none) {
  .action-btn {
    visibility: visible;
  }
}

/* 底部渐隐遮罩 */
.scroll-fade-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 10vh;
  pointer-events: none;
  background: linear-gradient(
    to top,
    var(--bg-elevated, #12121a),
    transparent
  );
  z-index: 2;
  transition: opacity 0.2s ease;
}

/* 浅色模式：使用更明显的渐隐 */
html:not(.dark) .scroll-fade-bottom {
  background: linear-gradient(
    to top,
    rgba(238, 242, 248, 0.95),
    rgba(238, 242, 248, 0.6) 50%,
    transparent
  );
}
</style>
