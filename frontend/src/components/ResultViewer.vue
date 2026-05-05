<template>
  <div class="result-viewer">
    <div v-if="!originalUrl" class="empty-state">
      <el-icon :size="48" color="#ccc"><Picture /></el-icon>
      <p>请先上传图像并开始诊断</p>
    </div>
    <div v-else class="canvas-container">
      <canvas ref="canvasRef" width="640" height="480"></canvas>
    </div>
    <div v-if="result" class="result-meta" style="margin-top: 8px; font-size: 13px; color: #666;">
      检出: {{ result.detection_count }} 个 | 最高置信度: {{ (result.max_confidence * 100).toFixed(1) }}% |
      耗时: {{ result.inference_time_ms.toFixed(1) }}ms
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  originalUrl: String,
  overlayUrl: String,
  viewMode: String,
  result: Object,
})

const canvasRef = ref(null)

function drawCanvas() {
  const canvas = canvasRef.value
  if (!canvas || !props.originalUrl) return
  const ctx = canvas.getContext('2d')
  const img = new Image()
  img.onload = () => {
    canvas.width = img.width
    canvas.height = img.height
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0)
    // TODO: draw boxes/masks based on result data and viewMode
  }
  img.src = props.originalUrl
}

onMounted(drawCanvas)
watch(() => props.originalUrl, drawCanvas)
watch(() => props.viewMode, drawCanvas)
</script>

<style scoped>
.result-viewer { min-height: 200px; }
.empty-state { text-align: center; padding: 60px 0; color: #999; }
.canvas-container canvas { max-width: 100%; border: 1px solid #eee; border-radius: 4px; }
</style>
