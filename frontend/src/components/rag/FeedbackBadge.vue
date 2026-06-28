<template>
  <div class="feedback-badge">
    <el-button-group size="small">
      <el-button
        :type="value === 1 ? 'success' : ''"
        :icon="Check"
        @click="setFeedback(true)"
        :disabled="disabled"
      >正确</el-button>
      <el-button
        :type="value === 0 ? 'danger' : ''"
        :icon="Close"
        @click="setFeedback(false)"
        :disabled="disabled"
      >错误</el-button>
    </el-button-group>
  </div>
</template>

<script setup>
import { Check, Close } from '@element-plus/icons-vue'

const props = defineProps({
  value: { type: [Number, null], default: null },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['feedback'])

function setFeedback(isCorrect) {
  emit('feedback', isCorrect)
}
</script>

<style scoped>
.feedback-badge {
  display: inline-flex;
  margin-top: 4px;
}
</style>
