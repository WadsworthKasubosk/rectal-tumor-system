<template>
  <el-dialog v-model="visible" title="PDF 报告预览" width="800px" @close="$emit('close')">
    <div v-if="loading" style="text-align: center; padding: 40px;">
      <el-icon :size="48" class="is-loading"><Loading /></el-icon>
      <p>正在生成报告...</p>
    </div>
    <div v-else-if="error" style="text-align: center; padding: 40px; color: #e74c3c;">
      {{ error }}
    </div>
    <div v-else style="text-align: center;">
      <p>报告已生成</p>
      <el-button type="primary" @click="downloadReport">下载 PDF</el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'

const props = defineProps({ caseId: Number, modelValue: Boolean })
const emit = defineEmits(['close', 'update:modelValue'])
const visible = ref(props.modelValue)
const loading = ref(false)
const error = ref('')

async function downloadReport() {
  try {
    const res = await api.get(`/reports/${props.caseId}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${props.caseId}.pdf`
    a.click()
  } catch (e) {
    error.value = '下载失败'
  }
}
</script>
