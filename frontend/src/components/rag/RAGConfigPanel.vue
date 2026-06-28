<template>
  <div class="rag-config-panel">
    <el-collapse v-model="activeNames">
      <el-collapse-item title="RAG 配置" name="config">
        <div class="config-items">
          <!-- Embedding 模型选择 -->
          <div class="config-item">
            <label class="config-label">Embedding 模型</label>
            <el-select
              v-model="localEmbeddingModel"
              size="small"
              style="width: 100%"
              @change="$emit('update:embeddingModel', $event)"
            >
              <el-option
                v-for="m in embeddingModels"
                :key="m.id"
                :label="m.name"
                :value="m.id"
              />
            </el-select>
          </div>
          <!-- Query 改写开关 -->
          <div class="config-item">
            <div class="config-toggle">
              <span>Query 改写</span>
              <el-switch
                v-model="localQueryRewriting"
                size="small"
                @change="$emit('update:enableQueryRewriting', $event)"
              />
            </div>
          </div>
          <!-- 混合检索开关 -->
          <div class="config-item">
            <div class="config-toggle">
              <span>混合检索 (BM25+向量)</span>
              <el-switch
                v-model="localHybridSearch"
                size="small"
                @change="$emit('update:enableHybridSearch', $event)"
              />
            </div>
          </div>
          <!-- 重排序开关 -->
          <div class="config-item">
            <div class="config-toggle">
              <span>重排序</span>
              <el-switch
                v-model="localReranking"
                size="small"
                @change="$emit('update:enableReranking', $event)"
              />
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  embeddingModel: { type: String, default: '' },
  embeddingModels: { type: Array, default: () => [] },
  enableQueryRewriting: { type: Boolean, default: true },
  enableHybridSearch: { type: Boolean, default: false },
  enableReranking: { type: Boolean, default: false },
})

defineEmits([
  'update:embeddingModel',
  'update:enableQueryRewriting',
  'update:enableHybridSearch',
  'update:enableReranking',
])

const activeNames = ref([])
const localEmbeddingModel = ref(props.embeddingModel)
const localQueryRewriting = ref(props.enableQueryRewriting)
const localHybridSearch = ref(props.enableHybridSearch)
const localReranking = ref(props.enableReranking)

// 监听 props 变化，同步到本地
watch(() => props.embeddingModel, (v) => { localEmbeddingModel.value = v })
watch(() => props.enableQueryRewriting, (v) => { localQueryRewriting.value = v })
watch(() => props.enableHybridSearch, (v) => { localHybridSearch.value = v })
watch(() => props.enableReranking, (v) => { localReranking.value = v })
</script>

<style scoped>
.rag-config-panel {
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
}

.config-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-label {
  font-size: 13px;
  color: #606266;
}

.config-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #606266;
}

@media (max-width: 768px) {
  .rag-config-panel {
    padding: 0 12px;
  }
}
</style>
