<template>
  <div class="intent-toggle">
    <el-tooltip content="开启后 Agent 自动识别意图，涉及知识库的问题调用 RAG 工具" placement="bottom">
      <el-switch
        v-model="enabled"
        active-text="意图识别"
        inactive-text=""
        inline-prompt
        style="--el-switch-on-color: #409eff"
      />
    </el-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'change'])

const enabled = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
    emit('change', val)
  },
})
</script>

<style scoped>
.intent-toggle {
  display: flex;
  align-items: center;
}
</style>
