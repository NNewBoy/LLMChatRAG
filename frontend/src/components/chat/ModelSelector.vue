<template>
  <el-select
    v-model="selectedValue"
    placeholder="选择模型"
    size="default"
    :disabled="disabled"
    style="width: 220px"
  >
    <el-option
      v-for="model in models"
      :key="model.id"
      :label="model.name + (model.multimodal ? ' (多模态)' : '')"
      :value="model.id"
    >
      <span>{{ model.name }}</span>
      <el-tag v-if="model.multimodal" size="small" type="success" style="margin-left: 8px">多模态</el-tag>
    </el-option>
  </el-select>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  models: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
    emit('change', val)
  },
})
</script>
