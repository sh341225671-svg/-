<template>
  <div id="app-root" :class="theme">
    <!-- 导航 -->
    <nav class="nav-bar">
      <div class="brand">
        <span class="logo-icon">⚡</span>
        <span>言灵</span>
      </div>
      <router-link to="/projects">📚 项目</router-link>
      <router-link to="/admin/agents">⚙️ Agent 管理</router-link>
      <router-link to="/workflow">🔧 流水线</router-link>
      <div class="spacer"></div>
      <button class="theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? '白天模式' : '夜晚模式'">
        {{ theme === 'dark' ? '☀️' : '🌙' }}
      </button>
    </nav>

    <!-- 主内容 -->
    <router-view />
    <div v-if="errorMsg" class="card" style="margin-top:8px;border-color:var(--red);padding:8px 12px">
      <div style="color:var(--red);font-size:12px;font-weight:600">❌ {{ errorMsg }}</div>
      <div v-if="errorDetails.detail" style="color:var(--text-dim);font-size:11px;margin-top:4px">{{ errorDetails.detail }}</div>
    </div>

    <!-- 底部 -->
    <div class="footer-bar">
      <span>⚡ 言灵创作引擎 · AI Writing Engine</span>
      <span style="font-size:11px;color:var(--text-dim)">创作者 · 督查者 · 读者 · 三位一体</span>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onErrorCaptured } from 'vue'

export default {
  name: 'App',
  setup() {
    const theme = ref(localStorage.getItem('lingxu-theme') || 'dark')

    const errorDetails = ref({})
    onErrorCaptured((err) => {
      console.error('Vue error:', err)
      if (err?.response) {
        // Axios error with response
        errorDetails.value = {
          message: `${err.config?.method?.toUpperCase()} ${err.config?.url}: ${err.response.status}`,
          detail: JSON.stringify(err.response.data).substring(0, 300),
          timestamp: new Date().toLocaleTimeString(),
        }
        errorMsg.value = `[${errorDetails.value.timestamp}] ${errorDetails.value.message}`
      } else if (err?.message) {
        errorMsg.value = `[${new Date().toLocaleTimeString()}] ${err.message}`
      } else {
        errorMsg.value = String(err)
      }
      // Auto-dismiss after 30s
      setTimeout(() => { errorMsg.value = ''; errorDetails.value = {} }, 30000)
      return false
    })
    function syncTheme(t) {
      document.documentElement.className = t
    }

    function toggleTheme() {
      theme.value = theme.value === 'dark' ? 'light' : 'dark'
      localStorage.setItem('lingxu-theme', theme.value)
      syncTheme(theme.value)
    }

    onMounted(() => syncTheme(theme.value))

    return { theme, toggleTheme, errorMsg, errorDetails }
  }
}
</script>

<style>
@import './style.css';
</style>
