<template>
  <div class="uploader">
    <el-upload
      class="upload-area"
      drag
      :auto-upload="false"
      :on-change="onFileChange"
      :show-file-list="false"
      accept="image/*"
    >
      <div v-if="!previewUrl" class="upload-placeholder">
        <el-icon :size="48" color="#ccc"><Upload /></el-icon>
        <p>拖拽图像到此处或点击上传</p>
      </div>
      <img v-else :src="previewUrl" class="preview-img" />
    </el-upload>
    <div v-if="uploading" style="margin-top: 10px; text-align: center;">
      <el-progress :percentage="100" :indeterminate="true" />
      <p style="color: #999;">上传中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const emit = defineEmits(['uploaded'])
const previewUrl = ref('')
const uploading = ref(false)

async function onFileChange(file) {
  previewUrl.value = URL.createObjectURL(file.raw)
  uploading.value = true

  try {
    const form = new FormData()
    form.append('file', file.raw)
    const { data } = await api.post('/upload', form)
    emit('uploaded', { imageId: data.id, url: data.url, filename: data.filename })
    ElMessage.success('上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
    previewUrl.value = ''
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.upload-area { width: 100%; }
.upload-placeholder { text-align: center; padding: 30px 0; color: #999; }
.preview-img { width: 100%; max-height: 300px; object-fit: contain; }
</style>
