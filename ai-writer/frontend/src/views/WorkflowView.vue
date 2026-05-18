<template>
  <div>
    <div class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px">
      <span style="font-size:16px;font-weight:700">🔧 创作流水线</span>
      <span class="text-dim" style="font-size:12px">点击章节卡片可查看详细内容 | 拖拽可更改状态</span>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="pipeline">
      <div v-for="stage in stages" :key="stage.key" class="pipeline-column">
        <div class="column-header" :style="{ background: stage.color }">
          <span class="column-icon">{{ stage.icon }}</span>
          <span class="column-title">{{ stage.label }}</span>
          <span class="column-count">{{ stage.chapters.length }}</span>
        </div>
        <div class="column-body"
          @dragover.prevent
          @drop="onDrop($event, stage.key)">
          <div v-for="ch in stage.chapters" :key="ch.id"
            class="chapter-card"
            :draggable="true"
            @dragstart="onDragStart($event, ch)"
            @click="openDetail(ch)">
            <div class="chapter-title">{{ ch.title }}</div>
            <div class="chapter-meta">
              <span>{{ ch.project_title }}</span>
              <span>📄 {{ (ch.content?.length || 0) }}字</span>
              <span v-if="ch.supervisor_report" class="score-badge">{{ (ch.supervisor_report.total_score || 0) }}分</span>
            </div>
          </div>
          <div v-if="!stage.chapters.length" class="column-empty">暂无章节</div>
        </div>
      </div>
    </div>

    <!-- 章节详情弹窗 -->
    <div v-if="showDetailModal && detailChapter" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal" style="max-width:700px;max-height:80vh;overflow-y:auto">
        <h4 style="margin-bottom:8px">📖 {{ detailChapter.title }}</h4>
        <div style="font-size:12px;color:var(--text-dim);margin-bottom:12px">
          <span>{{ detailChapter.project_title }}</span>
          <span class="tag" :class="'status-' + detailChapter.status" style="margin-left:8px">{{ statusLabel(detailChapter.status) }}</span>
          <span style="margin-left:8px">📄 {{ (detailChapter.content?.length || 0) }}字</span>
        </div>

        <div class="section-label" style="margin-bottom:6px">正文预览</div>
        <div v-if="detailChapter.content" style="font-size:13px;line-height:1.8;padding:12px;background:var(--bg);border-radius:var(--radius-sm);max-height:300px;overflow-y:auto;white-space:pre-wrap;margin-bottom:16px">{{ detailChapter.content.substring(0, 2000) }}{{ (detailChapter.content.length > 2000) ? '……' : '' }}</div>
        <div v-else style="margin-bottom:16px;padding:24px;background:var(--bg);border-radius:var(--radius-sm);text-align:center;color:var(--text-dim)">暂无正文内容</div>

        <div v-if="detailChapter.supervisor_report" style="margin-bottom:12px">
          <div class="section-label" style="margin-bottom:6px">🔍 督查报告</div>
          <div style="font-size:12px">
            <div v-for="c in (detailChapter.supervisor_report.checks || [])" :key="c.step"
              style="display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid var(--border)">
              <span :style="{color: (c.score || 0) >= 7 ? 'var(--green)' : (c.score || 0) >= 4 ? 'var(--yellow)' : 'var(--red)', fontWeight:600, minWidth:'120px'}">{{ c.label }}: {{ c.score }}/10</span>
              <span style="color:var(--text-dim);font-size:11px">{{ (c.detail || '').substring(0, 100) }}</span>
            </div>
            <div style="margin-top:8px;font-weight:600;font-size:13px">总分: {{ detailChapter.supervisor_report.total_score || 0 }} / 10</div>
          </div>
        </div>

        <div v-if="detailChapter.reader_report" style="margin-bottom:12px">
          <div class="section-label" style="margin-bottom:6px">📚 读者反馈</div>
          <div style="font-size:12px">
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px">
              <div v-for="(v, k) in (detailChapter.reader_report.scores || {})" :key="k"
                style="background:var(--bg);padding:6px 10px;border-radius:var(--radius-sm);text-align:center">
                <div style="font-size:10px;color:var(--text-dim)">{{ k }}</div>
                <div :style="{color: v >= 7 ? 'var(--green)' : v >= 4 ? 'var(--yellow)' : 'var(--red)', fontSize:'18px', fontWeight:700}">{{ v }}</div>
              </div>
            </div>
            <div v-if="detailChapter.reader_report.comments" style="color:var(--text-dim);padding:8px;background:var(--bg);border-radius:4px;line-height:1.6">{{ detailChapter.reader_report.comments }}</div>
          </div>
        </div>

        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
          <button class="btn btn-sm btn-outline" @click="showDetailModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 状态切换弹窗 -->
    <div v-if="showStatusModal" class="modal-overlay" @click.self="showStatusModal = false">
      <div class="modal" style="max-width:400px">
        <h4 style="margin-bottom:16px">修改章节状态</h4>
        <p style="font-size:13px;margin-bottom:12px"><strong>{{ selectedChapter?.title }}</strong></p>
        <div style="display:flex;flex-direction:column;gap:8px">
          <button v-for="s in stageOptions" :key="s.key"
            class="btn" :class="selectedChapter?.status === s.key ? 'btn-primary' : 'btn-outline'"
            @click="updateChapterStatus(selectedChapter, s.key)">
            {{ s.icon }} {{ s.label }}
          </button>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn btn-outline btn-sm" @click="showStatusModal = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../api'

const STAGES = [
  { key: 'draft', label: '草稿', icon: '📝', color: 'rgba(156,163,175,0.2)' },
  { key: 'writing', label: '写作中', icon: '✍️', color: 'rgba(59,130,246,0.2)' },
  { key: 'reviewing', label: '审校中', icon: '🔍', color: 'rgba(245,158,11,0.2)' },
  { key: 'reading', label: '读者反馈', icon: '📚', color: 'rgba(139,92,246,0.2)' },
  { key: 'completed', label: '已完成', icon: '✅', color: 'rgba(34,197,94,0.2)' },
]

export default {
  name: 'WorkflowView',
  setup() {
    const { getProjects, updateChapter } = useApi()
    const projects = ref([])
    const loading = ref(true)
    const showStatusModal = ref(false)
    const showDetailModal = ref(false)
    const selectedChapter = ref(null)
    const detailChapter = ref(null)
    const dragData = ref(null)

    const stageOptions = STAGES

    const stages = computed(() => {
      const map = {}
      for (const s of STAGES) {
        map[s.key] = { ...s, chapters: [] }
      }
      for (const p of projects.value) {
        for (const v of p.volumes || []) {
          for (const c of v.chapters || []) {
            const status = c.status || 'draft'
            // Parse JSON reports
            let report = null
            if (c.supervisor_report && typeof c.supervisor_report === 'string') {
              try { report = JSON.parse(c.supervisor_report) } catch(e) {}
            } else {
              report = c.supervisor_report
            }
            if (map[status]) {
              map[status].chapters.push({
                ...c,
                project_title: p.title,
                supervisor_report: report,
                reader_report: (typeof c.reader_report === 'string') ? (() => { try { return JSON.parse(c.reader_report) } catch(e) { return null } })() : c.reader_report
              })
            }
          }
        }
      }
      return Object.values(map)
    })

    async function loadData() {
      loading.value = true
      try {
        const res = await getProjects()
        projects.value = res.data
      } finally {
        loading.value = false
      }
    }

    function onDragStart(event, ch) {
      dragData.value = ch
      event.dataTransfer.effectAllowed = 'move'
    }

    async function onDrop(event, targetStatus) {
      if (!dragData.value) return
      const ch = dragData.value
      if (ch.status === targetStatus) return
      await updateChapter(ch.id, { status: targetStatus })
      dragData.value = null
      await loadData()
    }

    function openDetail(ch) {
      detailChapter.value = ch
      showDetailModal.value = true
    }

    function statusLabel(s) {
      const m = { draft: '草稿', writing: '写作中', reviewing: '审校中', reading: '读者反馈', completed: '已完成', approved: '已完成', rejected: '需修改' }
      return m[s] || s
    }

    async function updateChapterStatus(ch, status) {
      if (ch.status === status) {
        showStatusModal.value = false
        return
      }
      await updateChapter(ch.id, { status })
      showStatusModal.value = false
      await loadData()
    }

    onMounted(loadData)

    return {
      stages, loading, showStatusModal, showDetailModal,
      selectedChapter, detailChapter, stageOptions,
      onDragStart, onDrop, openDetail, updateChapterStatus, statusLabel
    }
  }
}
</script>

<style scoped>
.pipeline {
  display: flex; gap: 12px; overflow-x: auto;
  padding-bottom: 20px; min-height: 60vh;
}
.pipeline-column {
  flex: 1; min-width: 200px;
  background: var(--bg-card, #1a1a2e);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex; flex-direction: column;
}
.column-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-radius: var(--radius) var(--radius) 0 0;
  font-size: 13px; font-weight: 600;
}
.column-icon { font-size: 16px; }
.column-title { flex: 1; }
.column-count {
  background: rgba(0,0,0,0.2); border-radius: 10px;
  padding: 0 8px; font-size: 11px; font-weight: 700;
}
.column-body {
  flex: 1; padding: 8px;
  display: flex; flex-direction: column; gap: 6px;
}
.chapter-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px; padding: 10px 12px;
  cursor: pointer; transition: all 0.15s;
}
.chapter-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}
.chapter-title {
  font-size: 13px; font-weight: 600;
  margin-bottom: 4px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.chapter-meta {
  font-size: 11px; color: var(--text-dim);
  display: flex; gap: 8px;
}
.column-empty {
  font-size: 12px; color: var(--text-dim);
  text-align: center; padding: 24px 0;
}
.score-badge {
  background: rgba(245,158,11,0.15); color: var(--accent);
  padding: 0 6px; border-radius: 8px; font-size: 10px; font-weight: 700;
}
.tag { display:inline-block; padding:1px 6px; border-radius:8px; font-size:11px; font-weight:600; }
.status-draft { background: rgba(234,179,8,0.15); color: var(--yellow); }
.status-writing { background: rgba(59,130,246,0.15); color: var(--blue); }
.status-reviewing { background: rgba(139,92,246,0.15); color: #a78bfa; }
.status-reading { background: rgba(139,92,246,0.15); color: #a78bfa; }
.status-completed { background: rgba(34,197,94,0.15); color: var(--green); }
.status-approved { background: rgba(34,197,94,0.15); color: var(--green); }
.status-rejected { background: rgba(239,68,68,0.15); color: var(--red); }
</style>
