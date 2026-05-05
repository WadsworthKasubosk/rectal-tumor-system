<template>
  <div class="diagnosis-page">
    <el-row :gutter="20">
      <!-- Left: upload area -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>图像上传</template>
          <ImageUploader @uploaded="onImageUploaded" />
          <el-divider />
          <el-form label-width="80px">
            <el-form-item label="患者姓名">
              <el-input v-model="patientName" placeholder="请输入" />
            </el-form-item>
            <el-form-item label="性别">
              <el-radio-group v-model="patientGender">
                <el-radio label="男">男</el-radio>
                <el-radio label="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="年龄">
              <el-input-number v-model="patientAge" :min="0" :max="150" />
            </el-form-item>
            <el-form-item label="AI 模型">
              <el-select v-model="selectedModel" placeholder="选择模型">
                <el-option v-for="m in models" :key="m.name" :label="m.label" :value="m.name" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="runDiagnosis" :loading="inferLoading">
                开始 AI 诊断
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Center: result viewer -->
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header>影像结果</template>
          <el-radio-group v-model="viewMode" style="margin-bottom: 10px;">
            <el-radio-button label="original">原图</el-radio-button>
            <el-radio-button label="box">检测框</el-radio-button>
            <el-radio-button label="mask">分割</el-radio-button>
            <el-radio-button label="both">两者</el-radio-button>
          </el-radio-group>
          <ResultViewer
            :original-url="currentImageUrl"
            :overlay-url="overlayUrl"
            :view-mode="viewMode"
            :result="inferResult"
          />
        </el-card>
      </el-col>

      <!-- Right: detection list + report -->
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>检出列表 ({{ inferResult ? inferResult.detection_count : 0 }})</template>
          <div v-if="!inferResult" style="color: #999; text-align: center;">请上传图像并开始诊断</div>
          <div v-else-if="inferResult.detection_count === 0" style="color: #2ecc71; text-align: center;">
            未检出肿瘤
          </div>
          <div v-else>
            <el-table :data="inferResult.detections" size="small" max-height="300">
              <el-table-column type="index" label="#" width="30" />
              <el-table-column prop="confidence" label="置信度" width="80">
                <template #default="{ row }">{{ (row.confidence * 100).toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="位置" width="100">
                <template #default="{ row }">
                  {{ Math.round(row.x1) }},{{ Math.round(row.y1) }}
                </template>
              </el-table-column>
            </el-table>
            <el-divider />
            <el-button type="success" @click="generateReport" :disabled="!inferResult" style="width: 100%">
              生成 PDF 报告
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import ImageUploader from '@/components/ImageUploader.vue'
import ResultViewer from '@/components/ResultViewer.vue'

const patientName = ref('')
const patientGender = ref('男')
const patientAge = ref(0)
const selectedModel = ref('baseline')
const currentImageId = ref(null)
const currentImageUrl = ref('')
const overlayUrl = ref('')
const viewMode = ref('both')
const inferLoading = ref(false)
const inferResult = ref(null)
const models = ref([])

onMounted(async () => {
  try {
    const { data } = await api.get('/models')
    models.value = data
  } catch (e) { console.error(e) }
})

function onImageUploaded({ imageId, url }) {
  currentImageId.value = imageId
  currentImageUrl.value = url
  inferResult.value = null
}

async function runDiagnosis() {
  if (!currentImageId.value) {
    ElMessage.warning('请先上传图像')
    return
  }
  inferLoading.value = true
  try {
    const { data } = await api.post('/inference', {
      image_id: currentImageId.value,
      model_name: selectedModel.value,
    })
    inferResult.value = data
    overlayUrl.value = data.overlay_url || ''
    ElMessage.success(`诊断完成，耗时 ${data.inference_time_ms.toFixed(1)}ms`)
  } catch (e) {
    ElMessage.error('诊断失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    inferLoading.value = false
  }
}

async function generateReport() {
  if (!currentImageId.value) return
  try {
    await api.post(`/reports/${currentImageId.value}`, { doctor_notes: '' })
    ElMessage.success('报告生成成功')
  } catch (e) {
    ElMessage.error('报告生成失败')
  }
}
</script>

<style scoped>
.diagnosis-page { padding: 20px; }
</style>
