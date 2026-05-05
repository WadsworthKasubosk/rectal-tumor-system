<template>
  <div class="model-compare">
    <h2 style="margin-bottom: 16px;">四模型并排对比</h2>
    <p style="color: #909399; margin-bottom: 20px;">上传一张结肠镜图像，同时运行 Baseline / +P2 / +CBAM / +P2+CBAM 四个模型，对比诊断结果</p>

    <!-- Upload -->
    <el-card shadow="never" class="upload-card">
      <el-upload
        class="uploader"
        drag
        :auto-upload="false"
        :show-file-list="false"
        :on-change="onFileChange"
        accept="image/*"
      >
        <div v-if="!previewUrl">
          <el-icon :size="48" color="#ccc"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽图像到此处 或 <em>点击上传</em></div>
        </div>
        <img v-else :src="previewUrl" class="preview-img" />
      </el-upload>
      <div v-if="selectedFile" class="action-bar">
        <span>已选择：{{ selectedFile.name }}</span>
        <el-button type="primary" size="large" :loading="loading" @click="runCompare">
          {{ loading ? '4 模型推理中...' : '开始对比诊断' }}
        </el-button>
      </div>
    </el-card>

    <!-- Results -->
    <div v-if="compareData" class="results-section">
      <!-- 2x2 grid -->
      <el-row :gutter="16">
        <el-col v-for="(res, key) in compareData.results" :key="key" :xs="24" :sm="12" style="margin-bottom: 16px;">
          <el-card class="model-card" shadow="hover">
            <template #header>
              <div class="model-header">
                <span class="model-name">{{ res.model_label }}</span>
                <div class="model-badges">
                  <el-tag v-if="key === compareData.fastest_model" type="warning" size="small" effect="dark">⚡ 最快</el-tag>
                  <el-tag v-if="key === compareData.highest_conf_model" type="success" size="small" effect="dark">🎯 最高置信度</el-tag>
                </div>
              </div>
            </template>

            <div v-if="res.status === 'success'" class="result-body">
              <img
                v-if="res.overlay_url"
                :src="res.overlay_url"
                class="result-image"
                alt="分割结果"
              />
              <div class="metrics">
                <div class="metric">
                  <span class="label">检出数</span>
                  <span class="value">{{ res.detections }}</span>
                </div>
                <div class="metric">
                  <span class="label">最高置信度</span>
                  <span class="value highlight">{{ (res.max_confidence * 100).toFixed(1) }}%</span>
                </div>
                <div class="metric">
                  <span class="label">推理耗时</span>
                  <span class="value">{{ res.inference_time_ms }} ms</span>
                </div>
              </div>
            </div>
            <el-empty v-else :description="res.error" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>

      <!-- ECharts comparison chart -->
      <el-card class="chart-card" shadow="hover">
        <template #header>模型性能对比</template>
        <div ref="chartRef" class="chart"></div>
      </el-card>

      <!-- Known performance reference -->
      <el-card class="ref-card" shadow="hover">
        <template #header>📊 各模型在测试集上的 Dice 参考值</template>
        <el-table :data="diceTable" stripe size="small">
          <el-table-column prop="subset" label="子集" width="180" />
          <el-table-column prop="baseline" label="Baseline" />
          <el-table-column prop="exp2" label="+P2" />
          <el-table-column prop="exp3" label="+CBAM" />
          <el-table-column prop="exp4" label="+P2+CBAM" />
        </el-table>
      </el-card>

      <!-- Conclusion -->
      <el-alert :closable="false" type="info" show-icon class="conclusion">
        <template #title>本次对比摘要</template>
        <div>
          针对该图像，<b>{{ modelLabel(compareData.highest_conf_model) }}</b> 给出了最高的诊断置信度，
          <b>{{ modelLabel(compareData.fastest_model) }}</b> 推理速度最快。
          4 模型总耗时 <b>{{ compareData.total_time_ms }} ms</b>。
          <br /><br />
          综合 798 张测试集评估结果（见上表），Baseline 在所有子集上综合最稳定（Mean Dice 0.631），
          CBAM 在边界困难病例（CVC-300）上提升显著（+22%），P2+CBAM 是最佳折中方案。
          最终诊断请结合临床表现综合判断。
        </div>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/api'

const selectedFile = ref(null)
const previewUrl = ref('')
const loading = ref(false)
const compareData = ref(null)
const chartRef = ref(null)
let chartInstance = null

// Known per-subset Dice from evaluation
const diceTable = [
  { subset: 'CVC-300 (60张)', baseline: '0.517', exp2: '0.547', exp3: '0.631 ⬆', exp4: '0.576' },
  { subset: 'CVC-ClinicDB (62张)', baseline: '0.845', exp2: '0.796', exp3: '0.730', exp4: '0.756' },
  { subset: 'CVC-ColonDB (380张)', baseline: '0.626', exp2: '0.562', exp3: '0.597', exp4: '0.594' },
  { subset: 'ETIS-LaribPolypDB (196张)', baseline: '0.354', exp2: '0.291', exp3: '0.252', exp4: '0.341' },
  { subset: 'Kvasir (100张)', baseline: '0.814', exp2: '0.773', exp3: '0.760', exp4: '0.786' },
  { subset: '均值 (798张)', baseline: '0.631', exp2: '0.594', exp3: '0.594', exp4: '0.611' },
]

const modelLabels = {
  baseline: 'YOLO11s-seg Baseline',
  exp2_p2: '+P2 Enhancement',
  exp3_cbam: '+CBAM Attention',
  exp4_p2_cbam: '+P2 + CBAM',
}

function modelLabel(key) {
  return modelLabels[key] || key
}

function onFileChange(file) {
  selectedFile.value = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
  compareData.value = null
}

async function runCompare() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  loading.value = true
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    const { data } = await api.post('/inference/compare', form)
    compareData.value = data
    await nextTick()
    renderChart()
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || '未知错误'
    ElMessage.error('对比失败：' + msg)
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !compareData.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const entries = Object.entries(compareData.value.results)
  const labels = entries.map(([, r]) => r.model_label)
  const confs = entries.map(([, r]) => +(r.max_confidence * 100).toFixed(1))
  const times = entries.map(([, r]) => r.inference_time_ms)

  chartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['最高置信度 (%)', '推理耗时 (ms)'], bottom: 0 },
    grid: { left: '3%', right: '4%', top: '8%', bottom: '12%', containLabel: true },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: 15 } },
    yAxis: [
      { type: 'value', name: '置信度 (%)', max: 100 },
      { type: 'value', name: '耗时 (ms)' },
    ],
    series: [
      {
        name: '最高置信度 (%)', type: 'bar', data: confs,
        itemStyle: { color: '#409EFF', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 50,
      },
      {
        name: '推理耗时 (ms)', type: 'bar', yAxisIndex: 1, data: times,
        itemStyle: { color: '#E6A23C', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 50,
      },
    ],
  })
}
</script>

<style scoped>
.model-compare { padding: 20px; max-width: 1200px; margin: 0 auto; }
.upload-card { margin-bottom: 20px; }
.uploader { width: 100%; }
.preview-img { max-height: 260px; object-fit: contain; }
.action-bar { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding: 12px; background: #f5f7fa; border-radius: 4px; }
.model-card { height: 100%; }
.model-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; }
.model-name { font-weight: 600; font-size: 15px; }
.model-badges { display: flex; gap: 4px; }
.result-image { width: 100%; max-height: 260px; object-fit: contain; border-radius: 4px; background: #000; }
.metrics { display: flex; justify-content: space-around; margin-top: 12px; }
.metric { text-align: center; }
.metric .label { display: block; font-size: 12px; color: #909399; }
.metric .value { display: block; font-size: 20px; font-weight: 700; color: #303133; margin-top: 4px; }
.metric .value.highlight { color: #409EFF; }
.chart-card { margin-bottom: 16px; }
.chart { width: 100%; height: 340px; }
.ref-card { margin-bottom: 16px; }
.conclusion { margin-top: 16px; line-height: 1.8; }
</style>
