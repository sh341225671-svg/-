<template>
  <div>
    <div class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px;flex-wrap:wrap">
      <button class="btn btn-outline btn-sm" @click="$router.back()">← 返回</button>
      <div v-if="chapter" style="flex:1;min-width:200px">
        <span style="font-size:16px;font-weight:700">{{ chapter.title }}</span>
        <span class="tag" :class="'status-' + chapter.status" style="margin-left:8px">{{ statusLabel(chapter.status) }}</span>
        <span style="font-size:12px;color:var(--text-dim);margin-left:8px">v{{ chapter.version }}</span>
      </div>
      <button class="btn btn-sm" :class="autoMode ? 'btn-primary' : 'btn-outline'" @click="autoMode = !autoMode">
        {{ autoMode ? '🔮 全自动' : '✍️ 半自动' }}
      </button>
      <button class="btn" :class="pipelineRunning ? 'btn-disabled' : 'btn-accent'" @click="launchPipeline" :disabled="pipelineRunning" style="font-weight:700">
        {{ pipelineRunning ? '⏳ 创作中...' : '🚀 启动创作' }}
      </button>
    </div>

    <div v-if="!chapter" class="loading">加载中...</div>

    <template v-if="chapter">
      <!-- Pipeline 进度条 -->
      <div v-if="pipelineRunning" class="card" style="margin-bottom:12px">
        <div class="card-title">⏳ 创作流水线进度</div>
        <div class="pipeline-progress-outer">
          <div class="pipeline-progress-inner" :style="{ width: pipelinePercent + '%' }"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-dim);margin-bottom:6px">
          <span>{{ pipelinePercent }}%</span>
          <span>{{ pipelineSteps.filter(s => s.status === 'done').length }}/{{ pipelineSteps.length }}</span>
        </div>
        <div class="pipeline-steps">
          <div v-for="(step, i) in pipelineSteps" :key="i"
            class="step" :class="{ active: step.status === 'running', done: step.status === 'done', pending: step.status === 'pending' }">
            <div class="step-icon">{{ step.done ? '✅' : step.running ? '⏳' : step.icon }}</div>
            <div class="step-label">{{ step.label }}</div>
            <div v-if="step.detail" class="step-detail">{{ step.detail }}</div>
          </div>
        </div>
      </div>

      <!-- 全自动模式 -->
      <div v-if="autoMode" class="card">
        <div class="card-title">🔮 全自动写作</div>
        <div class="form-group">
          <label>写作需求 / 本章目标</label>
          <textarea v-model="writeRequest" rows="4" placeholder="描述本章需要写的内容、风格要求、关键转折点…"></textarea>
        </div>
        <button class="btn btn-primary" @click="startAutoWrite" :disabled="autoWriting || !writeRequest">
          {{ autoWriting ? '✍️ 创作中...' : '🚀 开始写作' }}
        </button>
        <div v-if="chapter.content && !autoWriting" style="margin-top:16px">
          <div class="card-title">📝 创作结果</div>
          <div class="content-preview" v-html="renderedContent"></div>
          <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
            <button class="btn btn-sm btn-outline" @click="editContent = true">✏️ 修改</button>
            <button class="btn btn-sm btn-primary" @click="saveChapter">💾 保存</button>
            <button class="btn btn-sm" style="background:rgba(245,158,11,0.15);color:var(--accent)" @click="triggerReview">🔍 提交督查</button>
            <button class="btn btn-sm" style="background:rgba(139,92,246,0.15);color:#a78bfa" @click="triggerRead">📚 读者模拟</button>
          </div>
        </div>
      </div>

      <!-- 半自动模式 + 督查/读者报告 -->
      <div v-if="!autoMode" class="row" style="gap:16px">
        <div class="col" style="flex:1;min-width:0">
          <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between">
              <span>✍️ 写作区域</span>
              <span style="font-weight:400;font-size:11px;color:var(--text-dim)">{{ wordCount }} 字</span>
            </div>
            <div class="form-group">
              <label>写作思路</label>
              <textarea v-model="chapter.writing_notes" rows="2" placeholder="本章的写作思路和要点…"></textarea>
            </div>
            <div class="form-group">
              <label>正文</label>
              <textarea v-model="chapter.content" rows="16" style="font-family:inherit;line-height:1.8;font-size:14px" placeholder="在此写作或粘贴草稿…"></textarea>
            </div>
            <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap">
              <button class="btn btn-sm btn-primary" @click="saveChapter">💾 保存</button>
              <button class="btn btn-sm btn-outline" @click="showRewriteDialog = true">🔄 重写</button>
              <button class="btn btn-sm" style="background:rgba(245,158,11,0.15);color:var(--accent)" @click="triggerReview">🔍 督查</button>
              <button class="btn btn-sm" style="background:rgba(139,92,246,0.15);color:#a78bfa" @click="triggerRead">📚 读者</button>
            </div>
          </div>

          <!-- 督查报告 -->
          <div v-if="chapter.supervisor_report" class="card" style="margin-top:12px">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center">
              <span>🔍 督查报告</span>
              <span style="font-size:13px;font-weight:700" :style="{color: (chapter.supervisor_report.total_score || 0) >= 7 ? 'var(--green)' : (chapter.supervisor_report.total_score || 0) >= 4 ? 'var(--yellow)' : 'var(--red)'}">总分 {{ (chapter.supervisor_report.total_score || 0) }}/10</span>
            </div>
            <div v-for="(c, i) in (chapter.supervisor_report.checks || [])" :key="i" class="check-item">
              <div style="display:flex;align-items:center;gap:8px">
                <span style="font-size:13px;font-weight:600;min-width:80px" :style="{color: (c.score || 0) >= 7 ? 'var(--green)' : (c.score || 0) >= 4 ? 'var(--yellow)' : 'var(--red)'}">{{ c.label }}: {{ c.score }}/10</span>
                <span style="font-size:12px;color:var(--text-dim)">{{ (c.detail || '').substring(0, 100) }}</span>
              </div>
            </div>
          </div>

          <!-- 读者反馈 -->
          <div v-if="chapter.reader_report" class="card" style="margin-top:12px">
            <div class="card-title">📚 读者反馈</div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px">
              <div v-for="(v, k) in (chapter.reader_report.scores || {})" :key="k" class="reader-item">
                <div class="dim">{{ k }}</div>
                <div class="score" :style="{color: v >= 7 ? 'var(--green)' : v >= 4 ? 'var(--yellow)' : 'var(--red)'}">{{ v }}</div>
              </div>
            </div>
            <div v-if="chapter.reader_report.comments" style="font-size:12px;color:var(--text-dim);padding:8px;background:var(--bg);border-radius:4px;line-height:1.6">{{ chapter.reader_report.comments }}</div>
          </div>
        </div>
      </div>

      <!-- Agent 对话面板 -->
      <div class="card" style="margin-top:12px;border:1px solid rgba(245,158,11,0.2)">
        <div class="card-title" style="display:flex;justify-content:space-between;align-items:center">
          <span>💬 与 Agent 对话</span>
          <div style="display:flex;gap:4px">
            <button v-for="t in agentTypes" :key="t.key" class="btn btn-xs" :class="chatAgent === t.key ? 'btn-primary' : 'btn-outline'"
              @click="chatAgent = t.key; loadChat()">{{ t.icon }} {{ t.label }}</button>
          </div>
        </div>
        <div class="chat-box" ref="chatBox">
          <div v-for="msg in chatMessages" :key="msg.id" class="chat-msg" :class="msg.role">
            <div class="chat-avatar">{{ msg.role === 'user' ? '👤' : chatAgentIcon(msg.agent_type) }}</div>
            <div class="chat-bubble">
              <div class="chat-bubble-header">
                <div style="font-size:11px;color:var(--text-dim);margin-bottom:2px">{{ msg.role === 'user' ? '你' : (msg.agent_type === 'creator' ? '创作者' : msg.agent_type === 'supervisor' ? '督查者' : '读者') }}</div>
                <button class="copy-btn" @click="copyText(msg.content)" title="复制内容">📋</button>
              </div>
              <div style="white-space:pre-wrap;font-size:13px;line-height:1.6">{{ msg.content }}</div>
              <div v-if="msg.metadata?.actions" style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap">
                <button v-for="act in msg.metadata.actions" :key="act.action" class="btn btn-xs btn-outline" @click="applyAction(act)">{{ act.label }}</button>
              </div>
            </div>
          </div>
          <div v-if="chatLoading" class="chat-msg agent">
            <div class="chat-avatar">{{ chatAgentIcon(chatAgent) }}</div>
            <div class="chat-bubble typing-indicator"><span></span><span></span><span></span></div>
          </div>
          <div v-if="chatMessages.length === 0 && !chatLoading" style="text-align:center;padding:24px;color:var(--text-dim);font-size:13px">
            与 Agent 对话，逐步构建世界观、角色、大纲、章节思路
          </div>
        </div>
        <div class="chat-input-row">
          <textarea v-model="chatInput" rows="2" placeholder="输入你的想法、需求、修改意见…" @keydown.enter="sendChat"></textarea>
          <button class="btn btn-primary" @click="sendChat" :disabled="!chatInput.trim() || chatLoading" style="align-self:flex-end;white-space:nowrap">发送</button>
        </div>
      </div>

      <!-- 重写对话框 -->
      <div v-if="showRewriteDialog" class="modal-overlay" @click.self="showRewriteDialog = false">
        <div class="modal" style="max-width:500px">
          <h4 style="margin-bottom:12px">🔄 段落重写</h4>
          <div class="form-group">
            <label>需要重写的段落</label>
            <textarea v-model="rewriteSectionText" rows="4" placeholder="粘贴需要重写的段落"></textarea>
          </div>
          <div class="form-group">
            <label>修改要求</label>
            <textarea v-model="rewriteInstruction" rows="3" placeholder="描述你想要什么方向的修改"></textarea>
          </div>
          <div style="display:flex;gap:8px;justify-content:flex-end">
            <button class="btn btn-outline btn-sm" @click="showRewriteDialog = false">取消</button>
            <button class="btn btn-primary btn-sm" @click="handleRewrite" :disabled="!rewriteSectionText">重写</button>
          </div>
        </div>
      </div>
      <!-- 编辑内容弹窗 -->
      <div v-if="editContent" class="modal-overlay" @click.self="editContent = false">
        <div class="modal" style="max-width:800px;max-height:80vh;overflow-y:auto">
          <h4 style="margin-bottom:12px">✏️ 修改内容</h4>
          <div class="form-group">
            <label>正文</label>
            <textarea v-model="chapter.content" rows="20" style="font-family:inherit;line-height:1.8;font-size:14px"></textarea>
          </div>
          <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
            <button class="btn btn-outline btn-sm" @click="editContent = false">取消</button>
            <button class="btn btn-primary btn-sm" @click="saveChapter(); editContent = false">保存</button>
          </div>
        </div>
      </div>
      <!-- Toast notification -->
      <div class="toast" :class="{ visible: toastVisible }">{{ toastMsg }}</div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useApi } from '../api'

export default {
  name: 'ChapterEditor',
  setup() {
    const route = useRoute()
    const api = useApi()
    const chapter = ref(null)
    const autoMode = ref(true)
    const writeRequest = ref('')
    const autoWriting = ref(false)
    const editContent = ref(false)
    const showRewriteDialog = ref(false)
    const rewriteSectionText = ref('')
    const rewriteInstruction = ref('')
    const toastMsg = ref('')
    const toastVisible = ref(false)

    function showToast(msg) {
      toastMsg.value = msg
      toastVisible.value = true
      setTimeout(() => { toastVisible.value = false }, 3000)
    }

    // Pipeline
    const pipelineRunning = ref(false)
    const pipelineSteps = ref([])
    const pipelinePercent = ref(0)

    // Chat
    const chatBox = ref(null)
    const chatMessages = ref([])
    const chatInput = ref('')
    const chatLoading = ref(false)
    const chatAgent = ref('creator')
    const agentTypes = [
      { key: 'creator', label: '创作者', icon: '✍️' },
      { key: 'supervisor', label: '督查者', icon: '🔍' },
      { key: 'reader', label: '读者', icon: '📚' },
    ]

    const wordCount = computed(() => (chapter.value?.content || '').replace(/\s/g, '').length)

    const renderedContent = computed(() => {
      if (!chapter.value?.content) return ''
      return chapter.value.content.replace(/\n/g, '<br>').replace(/#{1,6} (.+)/g, '<strong>$1</strong><br>')
    })

    function statusLabel(s) {
      const m = { draft: '草稿', writing: '写作中', review: '审校中', reviewing: '审校中', approved: '已完成', rejected: '需修改' }
      return m[s] || s
    }

    function chatAgentIcon(type) {
      return { creator: '✍️', supervisor: '🔍', reader: '📚' }[type] || '🤖'
    }

    async function loadChapter() {
      const res = await api.getChapter(route.params.id)
      chapter.value = res.data
    }

    async function loadChat() {
      try {
        // Need project_id - fetch chapter detail which has volume->project
        // Or fetch the parent volume to get project_id
        if (!chapter.value?.volume_id) return
        // Fetch the volume from chapter response or via separate API
        // For now, get project_id from chapter if available
        const pid = chapter.value.project_id || 0
        if (!pid) return
        const res = await api.getChatMessages(pid, chatAgent.value)
        chatMessages.value = res.data || []
        await nextTick()
        if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
      } catch(e) { /* ignore */ }
    }

    async function sendChat() {
      const msg = chatInput.value.trim()
      if (!msg || chatLoading.value) return
      chatInput.value = ''
      chatLoading.value = true
      try {
        const pid = chapter.value.project_id || 0
        const res = await api.sendChatMessage(pid, { agent_type: chatAgent.value, message: msg, section: 'chapters' })
        if (res.data) {
          chatMessages.value.push({
            id: Date.now(), role: 'user', agent_type: chatAgent.value, content: msg
          })
          chatMessages.value.push({
            id: Date.now() + 1, role: 'agent', agent_type: chatAgent.value,
            content: res.data.agent_reply?.content || '（无回复）',
            metadata: res.data.agent_reply?.actions || null
          })
          await nextTick()
          if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
        }
      } catch(e) {
        chatMessages.value.push({ id: Date.now(), role: 'agent', agent_type: chatAgent.value, content: '⚠️ 消息发送失败，请重试' })
      } finally { chatLoading.value = false }
    }

    async function applyAction(action) {
      try {
        const pid = chapter.value.project_id || 0
        await api.applyChatAction(pid, action)
        await loadChapter()
      } catch(e) { /* ignore */ }
    }

    async function saveChapter() {
      await api.updateChapter(chapter.value.id, { content: chapter.value.content, writing_notes: chapter.value.writing_notes })
    }

    async function startAutoWrite() {
      autoWriting.value = true
      try {
        const res = await api.autoWrite({
          project_id: chapter.value.project_id || 0,
          chapter_id: chapter.value.id,
          request: writeRequest.value
        })
        chapter.value.content = res.data.content || chapter.value.content
        await api.updateChapter(chapter.value.id, { content: chapter.value.content })
      } finally { autoWriting.value = false }
    }

    async function launchPipeline() {
      pipelineRunning.value = true
      pipelineSteps.value = [
        { icon: '✍️', label: '创作者写作', status: 'running', detail: '' },
        { icon: '🔍', label: '督查者审校', status: 'pending', detail: '' },
        { icon: '📚', label: '读者反馈', status: 'pending', detail: '' },
        { icon: '✅', label: '终端审核', status: 'pending', detail: '' },
      ]
      try {
        // Step 1: Write
        pipelineSteps.value[0].status = 'running'
        const writeRes = await api.autoWrite({
          project_id: chapter.value.project_id || 0,
          chapter_id: chapter.value.id,
          request: writeRequest.value || '自动创作本章'
        })
        await api.updateChapter(chapter.value.id, { content: writeRes.data.content || chapter.value.content })
        pipelineSteps.value[0].status = 'done'
        pipelineSteps.value[0].detail = `${(writeRes.data.content || '').length} 字`
        chapter.value.content = writeRes.data.content || chapter.value.content

        // Step 2: Review
        pipelineSteps.value[1].status = 'running'
        const reviewRes = await api.triggerReview(chapter.value.id)
        const report = reviewRes.data?.report || {}
        pipelineSteps.value[1].status = 'done'
        pipelineSteps.value[1].detail = `评分 ${report.total_score || 0}/10`

        // Step 3: Read
        pipelineSteps.value[2].status = 'running'
        const readRes = await api.triggerRead(chapter.value.id)
        const scores = readRes.data?.scores || {}
        pipelineSteps.value[2].status = 'done'
        pipelineSteps.value[2].detail = `${Object.keys(scores).length} 维度评分`

        // Step 4: Approve (terminal approval based on review score)
        pipelineSteps.value[3].status = 'running'
        const score = report.total_score || 0
        const verdict = score >= 7 ? 'approved' : score >= 4 ? 'needs_revision' : 'rejected'
        await api.updateChapter(chapter.value.id, { status: verdict === 'approved' ? 'approved' : 'review' })
        pipelineSteps.value[3].status = 'done'
        pipelineSteps.value[3].detail = `评分 ${score}/10 → ${verdict === 'approved' ? '✅通过' : verdict === 'needs_revision' ? '🔄修改' : '❌重写'}`

        await loadChapter()
      } catch(e) {
        pipelineSteps.value.forEach(s => {
          if (s.status === 'running') { s.status = 'error'; s.detail = '❌ 失败' }
        })
        showToast('⚠️ 流水线执行出错')
      } finally { pipelineRunning.value = false }
    }

    async function handleRewrite() {
      const res = await api.rewriteSection({
        content: rewriteSectionText.value, instruction: rewriteInstruction.value,
        chapter_id: chapter.value.id
      })
      if (res.data?.rewritten) {
        chapter.value.content = chapter.value.content.replace(rewriteSectionText.value, res.data.rewritten)
      }
      showRewriteDialog.value = false
      rewriteSectionText.value = ''
      rewriteInstruction.value = ''
    }

    function copyText(text) {
      navigator.clipboard.writeText(text).then(() => {}).catch(() => {
        const ta = document.createElement('textarea')
        ta.value = text
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      })
    }

    async function triggerReview() {
      await api.triggerReview(chapter.value.id)
      await loadChapter()
      showToast('✅ 已提交督查，等待结果...')
    }

    async function triggerRead() {
      await api.triggerRead(chapter.value.id)
      await loadChapter()
      showToast('✅ 读者模拟完成')
    }

    // 流水线状态轮询（每5秒检查 chapter 状态变化）
    let pollTimer = null
    let lastStatus = ''
    function startPolling() {
      lastStatus = chapter.value?.status || ''
      stopPolling()
      pollTimer = setInterval(async () => {
        if (!chapter.value?.id) return
        try {
          const res = await api.getChapter(chapter.value.id)
          const newChapter = res.data
          // 状态变更时自动刷新
          if (newChapter.status !== lastStatus) {
            lastStatus = newChapter.status
            chapter.value = newChapter
            showToast(`📌 章节状态更新: ${statusLabel(newChapter.status)}`)
            // 如果督查完成，自动回调创作者
            if (newChapter.status === 'review' || newChapter.status === 'reviewing') {
              if (newChapter.supervisor_report && Object.keys(newChapter.supervisor_report).length > 0) {
                showToast('🔔 收到督查反馈！请查看')
                // 督查反馈后自动触发下一轮 - 如果被驳回则通知创作者修改
                if (newChapter.status === 'review' || newChapter.status === 'reviewing') {
                  // 已在督查后，等待创作者手动修改
                }
              }
            }
            // 如果通过，自动启动下一轮创作循环
            if (newChapter.status === 'approved') {
              showToast('✅ 章节通过！可在项目中创建更多章节')
            }
          }
        } catch(e) { /* ignore poll errors */ }
      }, 5000)
    }
    function stopPolling() {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    // 创建章节后自动触发审查
    async function createAndReviewChapter(vid, order) {
      try {
        const res = await api.createChapter(vid, { title: `第${order + 1}章`, chapter_order: order + 1 })
        chapter.value = res.data
        lastStatus = chapter.value.status
        showToast('✅ 章节已创建，启动流水线...')
        await launchPipeline()
      } catch(e) {
        showToast('⚠️ 创建章节失败: ' + (e.message || ''))
      }
    }

    onMounted(async () => {
      await loadChapter()
      await loadChat()
      if (chapter.value?.id) {
        startPolling()
      }
    })

    // 组件卸载时停止轮询
    onUnmounted(() => {
      stopPolling()
    })

    return {
      chapter, autoMode, writeRequest, autoWriting, editContent,
      showRewriteDialog, rewriteSectionText, rewriteInstruction,
      wordCount, renderedContent, statusLabel, chatAgent, agentTypes,
      chatMessages, chatInput, chatLoading, chatBox,
      saveChapter, startAutoWrite, handleRewrite, triggerReview, triggerRead,
      launchPipeline, pipelineRunning, pipelineSteps, pipelinePercent,
      loadChat, sendChat, applyAction, chatAgentIcon, copyText,
      toastMsg, toastVisible, showToast
    }
  }
}
</script>

<style scoped>
.pipeline-steps { display:flex; gap:8px; margin-top:8px; flex-wrap:wrap; }
.step { flex:1; min-width:120px; padding:10px; border-radius:var(--radius-sm); text-align:center; border:1px solid var(--border); transition:all 0.3s; }
.step.active { border-color:var(--accent); background:rgba(245,158,11,0.08); }
.step.done { border-color:var(--green); background:rgba(34,197,94,0.08); }
.step.error { border-color:var(--red); background:rgba(239,68,68,0.08); }
.step.pending { opacity:0.4; }
.step-icon { font-size:24px; margin-bottom:4px; }
.step-label { font-size:12px; font-weight:600; }
.step-detail { font-size:10px; color:var(--text-dim); margin-top:2px; }
.chat-box { max-height:400px; overflow-y:auto; padding:12px; background:var(--bg); border-radius:var(--radius-sm); margin:8px 0; }
.chat-msg { display:flex; gap:8px; margin-bottom:12px; }
.chat-msg.agent { }
.chat-msg.user { flex-direction:row-reverse; }
.chat-avatar { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:16px; background:var(--bg-card); flex-shrink:0; }
.chat-bubble { max-width:80%; padding:10px 14px; border-radius:12px; background:var(--bg-card); border:1px solid var(--border); }
.chat-msg.user .chat-bubble { background:rgba(245,158,11,0.08); border-color:rgba(245,158,11,0.2); }
.chat-input-row { display:flex; gap:8px; align-items:flex-end; }
.chat-input-row textarea { flex:1; border:1px solid var(--border); background:var(--bg); color:var(--text); border-radius:var(--radius-sm); padding:8px; font-family:inherit; font-size:13px; resize:vertical; }
.chat-input-row textarea:focus { outline:none; border-color:var(--accent); }
.typing-indicator { display:flex; gap:4px; padding:8px 0; }
.typing-indicator span { width:6px; height:6px; border-radius:50%; background:var(--text-dim); animation:typing 1s infinite; }
.typing-indicator span:nth-child(2) { animation-delay:0.2s; }
.typing-indicator span:nth-child(3) { animation-delay:0.4s; }
@keyframes typing { 0%,60%,100% { opacity:0.3; transform:translateY(0); } 30% { opacity:1; transform:translateY(-4px); } }
.btn-accent { background:var(--accent); color:#fff; border:1px solid var(--accent); }
.btn-accent:hover { filter:brightness(1.1); }
.btn-disabled { opacity:0.5; cursor:not-allowed; }
.check-item { padding:6px 0; border-bottom:1px solid var(--border); }
.check-item:last-child { border-bottom:none; }
.content-preview { line-height:1.8; font-size:14px; padding:16px; background:var(--bg); border-radius:var(--radius-sm); }
.reader-item { background:var(--bg); border-radius:4px; padding:8px; text-align:center; min-width:70px; }
.reader-item .dim { font-size:10px; color:var(--text-dim); }
.reader-item .score { font-size:20px; font-weight:700; margin-top:2px; }
.status-draft { background:rgba(234,179,8,0.15); color:var(--yellow); }
.status-writing { background:rgba(59,130,246,0.15); color:var(--blue); }
.status-review { background:rgba(139,92,246,0.15); color:#a78bfa; }
.status-approved { background:rgba(34,197,94,0.15); color:var(--green); }
.status-rejected { background:rgba(239,68,68,0.15); color:var(--red); }
</style>
