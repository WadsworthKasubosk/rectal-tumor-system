<template>
  <div id="app">
    <el-container>
      <el-header v-if="showNav" class="app-header">
        <div class="nav-left">
          <span class="app-title">直肠肿瘤 AI 辅助诊断系统</span>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="route.path"
          router
          class="nav-menu"
          :ellipsis="false"
        >
          <el-menu-item index="/dashboard">仪表盘</el-menu-item>
          <el-menu-item index="/diagnosis">AI 诊断</el-menu-item>
          <el-menu-item index="/compare">模型对比</el-menu-item>
          <el-menu-item index="/cases">病例列表</el-menu-item>
          <el-menu-item index="/settings">系统设置</el-menu-item>
        </el-menu>
        <div class="nav-right">
          <el-button text @click="logout" v-if="showNav">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const showNav = computed(() => route.path !== '/login')

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style>
body { margin: 0; font-family: "Microsoft YaHei", sans-serif; }
#app { min-height: 100vh; background: #f0f2f5; }
.app-header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 56px;
}
.nav-left { margin-right: 24px; }
.app-title { font-size: 16px; font-weight: 700; color: #303133; white-space: nowrap; }
.nav-menu { flex: 1; border-bottom: none !important; }
.nav-right { margin-left: auto; }
</style>
