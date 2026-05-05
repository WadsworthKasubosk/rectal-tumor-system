<template>
  <div class="case-list-page">
    <el-card shadow="hover">
      <template #header>
        <el-row justify="space-between" align="middle">
          <span>病例列表</span>
          <el-input v-model="search" placeholder="搜索患者姓名" style="width: 240px;" clearable @clear="fetchCases" @keyup.enter="fetchCases" />
        </el-row>
      </template>
      <el-table :data="cases" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="patient_name" label="患者姓名" />
        <el-table-column prop="patient_gender" label="性别" width="60" />
        <el-table-column prop="patient_age" label="年龄" width="60" />
        <el-table-column prop="exam_date" label="检查日期" width="120" />
        <el-table-column prop="diagnosis_count" label="诊断次数" width="80" />
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.latest_result === 'positive' ? 'danger' : 'success'" size="small">
              {{ row.latest_result === 'positive' ? '阳性' : '阴性' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/cases/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="onPageChange"
        style="margin-top: 16px; justify-content: center;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const cases = ref([])
const loading = ref(false)
const search = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

onMounted(() => fetchCases())

async function fetchCases() {
  loading.value = true
  try {
    const { data } = await api.get('/cases', { params: { page: page.value, page_size: pageSize.value, search: search.value } })
    cases.value = data.items
    total.value = data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function onPageChange(p) {
  page.value = p
  fetchCases()
}
</script>

<style scoped>
.case-list-page { padding: 20px; }
</style>
