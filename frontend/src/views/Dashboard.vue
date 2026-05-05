<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>诊断结果分布</template>
          <div ref="pieChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>模型使用统计</template>
          <div ref="modelChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import * as echarts from 'echarts'

const statCards = ref([
  { label: '总病例数', value: 0 },
  { label: '总诊断数', value: 0 },
  { label: '阳性检出', value: 0 },
  { label: '平均置信度', value: '0.00' },
])

const pieChart = ref(null)
const modelChart = ref(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/stats/dashboard')
    statCards.value[0].value = data.total_cases
    statCards.value[1].value = data.total_diagnoses
    statCards.value[2].value = data.positive_count
    statCards.value[3].value = data.avg_confidence.toFixed(2)

    // Pie — positive/negative
    const pie = echarts.init(pieChart.value)
    pie.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: [
          { value: data.positive_count, name: '阳性', itemStyle: { color: '#e74c3c' } },
          { value: data.negative_count, name: '阴性', itemStyle: { color: '#2ecc71' } },
        ],
      }],
    })

    // Bar — model usage
    const bar = echarts.init(modelChart.value)
    bar.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Object.keys(data.model_usage) },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: Object.values(data.model_usage), itemStyle: { color: '#667eea' } }],
    })
  } catch (e) {
    console.error('Failed to load dashboard stats', e)
  }
})
</script>

<style scoped>
.dashboard { padding: 20px; }
.stat-card { text-align: center; padding: 10px; }
.stat-value { font-size: 28px; font-weight: bold; color: #667eea; }
.stat-label { font-size: 14px; color: #999; margin-top: 4px; }
</style>
