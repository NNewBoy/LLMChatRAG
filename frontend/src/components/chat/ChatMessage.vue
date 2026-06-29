<template>
  <div class="chat-message" :class="{ 'is-user': message.role === 'user', 'is-assistant': message.role === 'assistant' }">
    <div class="message-avatar">
      <el-avatar :size="32" :style="{ background: message.role === 'user' ? '#409eff' : '#67c23a' }">
        {{ message.role === 'user' ? '我' : 'AI' }}
      </el-avatar>
    </div>
    <div class="message-body">
      <!-- 思考过程 -->
      <ChatThinking
        v-if="message.thinking"
        :content="message.thinking"
        :is-streaming="isStreaming && message.role === 'assistant'"
      />
      <!-- 工具调用 -->
      <ChatToolCall
        v-if="message.tool_calls"
        :content="message.tool_calls"
      />
      <!-- 消息内容 -->
      <div v-if="isWaiting" class="message-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>AI 正在思考...</span>
      </div>
      <div class="message-content" v-else v-html="renderedContent"></div>
      <!-- 操作按钮 -->
      <div class="message-actions" v-if="message.role === 'assistant' && !isStreaming">
        <el-button-group size="small">
          <el-button text size="small" @click="$emit('regenerate', message.id)">
            <el-icon><RefreshRight /></el-icon> 重新生成
          </el-button>
          <el-button text size="small" @click="$emit('followup', message.id)">
            <el-icon><ChatDotRound /></el-icon> 追问
          </el-button>
          <el-button text size="small" @click="$emit('delete', message.id)">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
          <el-button
            text size="small"
            :type="message.is_correct === 1 ? 'success' : ''"
            @click="$emit('feedback', { id: message.id, isCorrect: true })"
            v-if="showFeedback && message.id && !message.id.startsWith('temp')"
          >
            <el-icon><Check /></el-icon> 正确
          </el-button>
          <el-button
            text size="small"
            :type="message.is_correct === 0 ? 'danger' : ''"
            @click="$emit('feedback', { id: message.id, isCorrect: false })"
            v-if="showFeedback && message.id && !message.id.startsWith('temp')"
          >
            <el-icon><Close /></el-icon> 错误
          </el-button>
        </el-button-group>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import { RefreshRight, ChatDotRound, Delete, Check, Close, Loading } from '@element-plus/icons-vue'
import ChatThinking from './ChatThinking.vue'
import ChatToolCall from './ChatToolCall.vue'

const props = defineProps({
  message: { type: Object, required: true },
  isStreaming: { type: Boolean, default: false },
  showFeedback: { type: Boolean, default: false },
})

defineEmits(['regenerate', 'followup', 'delete', 'feedback'])

// 配置 marked
marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  try {
    return marked(props.message.content)
  } catch {
    return props.message.content
  }
})

// 助手流式输出但尚未收到任何内容时，显示加载提示
const isWaiting = computed(() =>
  props.isStreaming &&
  props.message.role === 'assistant' &&
  !props.message.content &&
  !props.message.thinking &&
  !props.message.tool_calls
)
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 0;
}

/* 用户消息：靠右 */
.chat-message.is-user {
  flex-direction: row-reverse;
}

.chat-message.is-user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.chat-message.is-user .message-content {
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px 12px 2px 12px;
  padding: 10px 14px;
  display: inline-block;
  max-width: 100%;
}

.message-avatar {
  flex-shrink: 0;
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary, #f8fafc);
  word-break: break-word;
}

.message-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-muted, #94a3b8);
  padding: 4px 0;
}

.message-loading .is-loading {
  animation: rotate 1.2s linear infinite;
}

@keyframes rotate {
  to {
    transform: rotate(360deg);
  }
}

.message-content :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--glass-border, rgba(255,255,255,0.1));
  border-radius: var(--radius-md, 12px);
  padding: 12px;
  overflow-x: auto;
}

.message-content :deep(code) {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
}

.message-content :deep(p) {
  margin: 8px 0;
}

.message-actions {
  margin-top: 8px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.chat-message:hover .message-actions {
  opacity: 1;
}
</style>
