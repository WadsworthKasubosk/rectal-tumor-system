<template>
  <div class="case-detail-page">
    <el-button @click="$router.push('/cases')" style="margin-bottom: 16px;">← 返回列表</el-button>
    <el-card shadow="hover" v-loading="loading">
      <template #header>病例详情 #{{ caseId }}</template>
      <el-descriptions v-if="detail" :column="3" border>
        <el-descriptions-item label="患者姓名">{{ detail.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ detail.patient_gender || '—' }}</el-descriptions-item>
        <el-descriptions-item label="年龄">{{ detail.patient_age || '—' }}</el-descriptions-item>
        <el-descriptions-item label="检查日期">{{ detail.exam_date }}</el-descriptions-item>
        <el-descriptions-item label="检查类型">{{ detail.exam_type }}</el-descriptions-item>
        <el-descriptions-item label="主治医生">{{ detail.doctor_name }}</el-descriptions-item>
      </el-descriptions>

      <h3 style="margin-top: 20px;">诊断记录</h3>
      <el-table :data="detail?.diagnoses || []" stripe>
        <el-table-column prop="id" label="ID" width="50" />
        <el-table-column prop="model_name" label="模型" />
        <el-table-column prop="detection_count" label="检出数" />
        <el-table-column label="最高置信度">
          <template #default="{ row }">{{ (row.max_confidence * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="inference_time_ms" label="耗时 (ms)" />
        <el-table-column prop="created_at" label="诊断时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

const route = useRoute()
const caseId = route.params.id
const detail = ref(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.get(`/cases/${caseId}`)
    detail.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.case-detail-page { padding: 20px; }
</style>
