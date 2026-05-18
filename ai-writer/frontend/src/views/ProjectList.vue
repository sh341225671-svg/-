<template>
  <div>
    <div class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px">
      <span style="font-size:16px;font-weight:700">📚 我的项目</span>
      <button class="btn btn-primary btn-sm" @click="showCreate = true" style="margin-left:auto">➕ 新建项目</button>
    </div>

    <!-- 创建对话框 -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h3 style="margin-bottom:16px">📖 新建项目</h3>
        <div class="form-group">
          <label>项目名称 *</label>
          <input v-model="form.title" placeholder="输入小说名称" />
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label>类型</label>
            <select v-model="form.genre" style="width:100%">
              <option>玄幻</option><option>推理</option><option>言情</option>
              <option>历史</option><option>都市</option><option>科幻</option><option>其他</option>
            </select>
          </div>
          <div class="form-group" style="flex:1">
            <label>目标字数</label>
            <input v-model.number="form.word_goal" placeholder="如 500000" />
          </div>
        </div>
        <div class="form-group">
          <label>主控思想（核心命题）</label>
          <textarea v-model="form.core_theme" rows="2" placeholder="一句话定义小说的核心命题，例如「生命的韧性高于一切苦难」" />
        </div>
        <div class="form-group">
          <label>目标读者</label>
          <input v-model="form.target_audience" placeholder="如：网文读者、女性向、悬疑爱好者" />
        </div>

        <div v-if="agents.length > 0" class="agent-selection-panel">
          <div class="panel-label">🤖 选择项目 Agent（选配）</div>
          <div class="text-dim" style="font-size:11px;margin-bottom:8px">写作/督查/阅读时将使用选定 Agent 的人设与能力</div>
          <div class="agent-type-group" v-for="(list, type) in groupedAgents" :key="type">
            <div class="type-header">
              <span class="type-icon">{{ type === 'creator' ? '✍️' : type === 'supervisor' ? '🔍' : '📚' }}</span>
              <span class="type-name">{{ type === 'creator' ? '创作者' : type === 'supervisor' ? '督查者' : '读者' }}</span>
              <span class="type-count">{{ list.length }}</span>
            </div>
            <div v-if="list.length === 0" class="type-empty">暂无该类 Agent，可去 ⚙️ 管理中心创建</div>
            <div v-for="a in list" :key="a.id" class="agent-card" :class="{ selected: form.agent_ids.includes(a.id) }" @click="toggleAgent(a.id)">
              <div class="agent-check">
                <div class="checkbox" :class="{ checked: form.agent_ids.includes(a.id) }">
                  <span v-if="form.agent_ids.includes(a.id)">✓</span>
                </div>
              </div>
              <div class="agent-info">
                <div class="agent-card-name">{{ a.name }}</div>
                <div class="agent-card-desc">{{ (a.system_prompt || '').substring(0, 60) }}{{ (a.system_prompt?.length || 0) > 60 ? '…' : '' }}</div>
                <div class="agent-card-tags">
                  <span v-for="cap in (a.capabilities || []).slice(0, 3)" :key="cap" class="mini-tag">{{ cap }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn btn-outline btn-sm" @click="showCreate = false">取消</button>
          <button class="btn btn-primary btn-sm" @click="handleCreate" :disabled="!form.title">创建项目</button>
        </div>
      </div>
    </div>

    <!-- 项目列表 -->
    <div v-if="projects.length === 0" class="empty-state">
      <div class="icon">📖</div>
      <div class="title">还没有项目</div>
      <div class="desc">点击「新建项目」开始你的第一部作品</div>
    </div>

    <div v-for="p in projects" :key="p.id" class="project-card">
      <div style="cursor:pointer" @click="$router.push('/projects/' + p.id)">
        <div class="project-header">
          <span class="project-title">{{ p.title }}</span>
          <span class="tag" :class="'status-' + p.status">
            {{ p.status === 'draft' ? '草稿' : p.status === 'active' ? '创作中' : '已完成' }}
          </span>
        </div>
        <div class="project-meta">
          <span>{{ genreIcon(p.genre) }} {{ p.genre }}</span>
          <span v-if="p.word_goal">🎯 {{ (p.word_goal / 10000).toFixed(1) }}万字</span>
          <span>📅 {{ formatDate(p.updated_at) }}</span>
        </div>
        <div v-if="p.core_theme" class="project-theme">💡 {{ p.core_theme }}</div>
        <div class="project-stats">
          <span>📦 {{ p.volumes?.length || 0 }} 卷</span>
          <span>👤 {{ p.characters?.length || 0 }} 角色</span>
        </div>
      </div>
      <button class="project-delete-btn" @click="handleDelete(p)" title="删除项目">🗑️</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../api'

export default {
  name: 'ProjectList',
  setup() {
    const { getProjects, createProject, deleteProject, getAgentConfigs } = useApi()
    const projects = ref([])
    const agents = ref([])
    const showCreate = ref(false)
    const form = ref({ title: '', genre: '玄幻', core_theme: '', target_audience: '', word_goal: null, agent_ids: [] })

    async function loadProjects() {
      const res = await getProjects()
      projects.value = res.data
    }

    async function handleCreate() {
      await createProject({ ...form.value, agent_ids: form.value.agent_ids?.length ? form.value.agent_ids : undefined })
      showCreate.value = false
      form.value = { title: '', genre: '玄幻', core_theme: '', target_audience: '', word_goal: null, agent_ids: [] }
      await loadProjects()
    }

    const groupedAgents = computed(() => {
      const groups = { creator: [], supervisor: [], reader: [] }
      for (const a of agents.value) {
        if (a.is_active !== false) {
          if (groups[a.agent_type]) groups[a.agent_type].push(a)
        }
      }
      return groups
    })

    function toggleAgent(id) {
      const idx = form.value.agent_ids.indexOf(id)
      if (idx >= 0) form.value.agent_ids.splice(idx, 1)
      else form.value.agent_ids.push(id)
    }

    function formatDate(d) {
      if (!d) return ''
      return new Date(d).toLocaleDateString('zh-CN')
    }

    function genreIcon(g) {
      const icons = { '玄幻': '🔥', '推理': '🔍', '言情': '💕', '历史': '📜', '都市': '🏙️', '科幻': '🚀' }
      return icons[g] || '📖'
    }

    async function handleDelete(p) {
      if (!confirm(`确定删除项目「${p.title}」吗？此操作不可撤销。`)) return
      await deleteProject(p.id)
      await loadProjects()
    }

    onMounted(async () => {
      await loadProjects()
      try {
        const res = await getAgentConfigs()
        agents.value = res.data || []
      } catch(e) {}
    })

    return { projects, agents, showCreate, form, groupedAgents, handleCreate, handleDelete, toggleAgent, formatDate, genreIcon }
  }
}
</script>

<style scoped>
.project-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.project-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}
.project-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.project-title { font-size: 18px; font-weight: 700; flex: 1; }
.project-meta { font-size: 12px; color: var(--text-dim); display: flex; gap: 12px; margin-bottom: 4px; }
.project-theme { font-size: 12px; color: var(--accent); padding: 4px 8px; background: rgba(245,158,11,0.08); border-radius: 4px; margin-bottom: 6px; }
.project-stats { font-size: 12px; color: var(--text-dim); display: flex; gap: 16px; }

.agent-type-group {
  background: var(--bg); border-radius: var(--radius-sm);
  padding: 8px 10px; margin-bottom: 6px;
}
.agent-option {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 0; font-size: 12px; cursor: pointer;
}
.agent-option input[type="checkbox"] { accent-color: var(--accent); }

.status-draft { background: rgba(234,179,8,0.15); color: var(--yellow); }
.status-active { background: rgba(34,197,94,0.15); color: var(--green); }
.status-completed { background: rgba(59,130,246,0.15); color: var(--blue); }

/* Agent selection panel */
.agent-selection-panel {
  margin-top: 12px;
  padding: 14px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.panel-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.type-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.type-icon { font-size: 16px; }
.type-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}
.type-count {
  font-size: 10px;
  color: var(--text-dim);
  background: var(--bg-card);
  padding: 0 6px;
  border-radius: 8px;
  line-height: 16px;
}
.type-empty {
  font-size: 11px;
  color: var(--text-dim);
  padding: 6px 10px;
  font-style: italic;
}
.agent-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  margin-bottom: 4px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}
.agent-card:hover {
  background: var(--bg-hover);
  border-color: var(--border);
}
.agent-card.selected {
  background: rgba(245,158,11,0.06);
  border-color: rgba(245,158,11,0.25);
}
.agent-check {
  flex-shrink: 0;
  padding-top: 2px;
}
.checkbox {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  font-size: 11px;
  color: #fff;
}
.checkbox.checked {
  background: var(--accent);
  border-color: var(--accent);
}
.agent-info { flex: 1; min-width: 0; }
.agent-card-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.agent-card-desc {
  font-size: 11px;
  color: var(--text-dim);
  margin-top: 1px;
  line-height: 1.4;
}
.agent-card-tags {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.mini-tag {
  background: rgba(59,130,246,0.1);
  color: var(--blue);
  padding: 0 6px;
  border-radius: 8px;
  font-size: 10px;
  line-height: 18px;
}
.agent-type-group { margin-bottom: 10px; }
.agent-type-group:last-child { margin-bottom: 0; }
</style>
