<template>
  <div class="settings-page">
    <el-card shadow="hover">
      <template #header>系统设置</template>
      <el-form label-width="120px">
        <el-form-item label="当前模型">
          <el-select v-model="currentModel" placeholder="选择模型">
            <el-option v-for="m in models" :key="m.name" :label="m.label" :value="m.name">
              <span>{{ m.label }}</span>
              <el-tag :type="m.available ? 'success' : 'danger'" size="small" style="margin-left: 8px;">
                {{ m.available ? `${m.size_mb} MB` : '不可用' }}
              </el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="置信度阈值">
          <el-slider v-model="confThreshold" :min="0.01" :max="0.99" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="IoU 阈值">
          <el-slider v-model="iouThreshold" :min="0.1" :max="0.9" :step="0.05" show-input />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const models = ref([])
const currentModel = ref('baseline')
const confThreshold = ref(0.25)
const iouThreshold = ref(0.45)

onMounted(async () => {
  try {
    const { data } = await api.get('/models')
    models.value = data
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.settings-page { padding: 20px; max-width: 600px; }
</style>
