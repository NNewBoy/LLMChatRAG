<template>
  <div class="image-upload">
    <el-upload
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      accept="image/*"
    >
      <el-button :icon="Picture" circle :disabled="disabled" title="上传图片" />
    </el-upload>
    <div v-if="imagePreview" class="image-preview">
      <img :src="imagePreview" alt="preview" />
      <el-button :icon="Close" circle size="small" class="remove-btn" @click="removeImage" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Picture, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: String, default: null },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const imagePreview = ref(null)

watch(() => props.modelValue, (val) => {
  imagePreview.value = val
})

function handleBeforeUpload(file) {
  if (!file.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    const base64 = e.target.result
    imagePreview.value = base64
    emit('update:modelValue', base64)
  }
  reader.readAsDataURL(file)
  return false
}

function removeImage() {
  imagePreview.value = null
  emit('update:modelValue', null)
}
</script>

<style scoped>
.image-upload {
  display: flex;
  align-items: center;
  gap: 8px;
}
.image-preview {
  position: relative;
  width: 40px;
  height: 40px;
}
.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}
.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
}
</style>
