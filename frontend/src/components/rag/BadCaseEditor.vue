<template>
  <div class="bad-case-editor">
    <div class="editor-header">
      <h3>错题集编辑</h3>
      <el-button text :icon="Refresh" @click="$emit('refresh')">刷新</el-button>
    </div>
    <el-empty v-if="badCases.length === 0" description="暂无错题" />
    <div v-else class="bad-case-list">
      <el-card
        v-for="bc in badCases"
        :key="bc.id"
        class="bad-case-card"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <span class="question-text">{{ bc.question }}</span>
            <el-button
              text
              size="small"
              :icon="Delete"
              @click="$emit('delete', bc.id)"
            />
          </div>
        </template>
        <div class="bad-case-content">
          <div class="wrong-answer">
            <label>错误答案:</label>
            <div class="answer-text">{{ bc.wrong_answer }}</div>
          </div>
          <div class="correct-answer">
            <label>正确答案:</label>
            <el-input
              v-model="editMap[bc.id].correct_answer"
              type="textarea"
              :rows="3"
              placeholder="请输入正确的答案"
              @change="updateField(bc.id)"
            />
          </div>
          <div class="example-toggle">
            <span>作为范例传给 LLM:</span>
            <el-switch
              v-model="editMap[bc.id].use_as_example"
              @change="updateField(bc.id)"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Refresh, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  badCases: { type: Array, default: () => [] },
})

const emit = defineEmits(['refresh', 'delete', 'update'])

// 编辑状态映射
const editMap = reactive({})

// 初始化/同步编辑数据
watch(() => props.badCases, (cases) => {
  cases.forEach(bc => {
    if (!editMap[bc.id]) {
      editMap[bc.id] = {
        correct_answer: bc.correct_answer || '',
        use_as_example: bc.use_as_example || false,
      }
    }
  })
}, { immediate: true, deep: true })

function updateField(badCaseId) {
  const data = editMap[badCaseId]
  if (data) {
    emit('update', {
      id: badCaseId,
      correct_answer: data.correct_answer,
      use_as_example: data.use_as_example,
    })
  }
}
</script>

<style scoped>
.bad-case-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 0 12px;
}

.editor-header h3 {
  margin: 0;
  font-size: 16px;
}

.bad-case-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.bad-case-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-text {
  font-weight: 500;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bad-case-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bad-case-content label {
  font-size: 13px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
}

.answer-text {
  font-size: 13px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 8px;
  border-radius: 4px;
  max-height: 100px;
  overflow-y: auto;
}

.example-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

@media (max-width: 768px) {
  .bad-case-editor {
    padding: 8px;
  }
}
</style>
