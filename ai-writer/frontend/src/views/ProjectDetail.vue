<template>
  <div>
    <div class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px">
      <button class="btn btn-outline btn-sm" @click="$router.push('/projects')">← 返回</button>
      <span style="font-size:18px;font-weight:700">{{ project?.title || '加载中...' }}</span>
      <span class="tag" :class="'status-' + project?.status" v-if="project">
        {{ project.status === 'draft' ? '草稿' : project.status === 'active' ? '创作中' : '已完成' }}
      </span>
      <div class="spacer"></div>
      <button class="btn btn-sm" :class="project?.status === 'active' ? 'btn-outline' : 'btn-primary'"
        @click="toggleStatus" v-if="project">
        {{ project.status === 'active' ? '暂停' : '开始创作' }}
      </button>
    </div>

    <div v-if="!project && !loadError" class="loading">加载中...</div>
    <div v-if="loadError" class="empty-state">
      <div class="icon">⚠️</div>
      <div class="title">加载失败</div>
      <div class="desc">{{ loadError }}</div>
      <button class="btn btn-primary btn-sm" @click="$router.push('/projects')" style="margin-top:12px">返回项目列表</button>
    </div>
    <div v-if="loadError" class="empty-state">
      <div class="icon">⚠️</div>
      <div class="title">加载失败</div>
      <div class="desc">{{ loadError }}</div>
      <button class="btn btn-primary btn-sm" @click="$router.push('/projects')" style="margin-top:12px">返回项目列表</button>
    </div>

    <template v-if="project">
      <div class="tabs">
        <div class="tab" :class="{active: tab === 'overview'}" @click="tab = 'overview'">📋 概览</div>
        <div class="tab" :class="{active: tab === 'outline'}" @click="tab = 'outline'">📖 大纲</div>
        <div class="tab" :class="{active: tab === 'characters'}" @click="tab = 'characters'">👤 角色</div>
        <div class="tab" :class="{active: tab === 'chapters'}" @click="tab = 'chapters'">📝 章节</div>
        <div class="tab" :class="{active: tab === 'world'}" @click="tab = 'world'">🌍 世界</div>
      </div>

      <!-- 概览 -->
      <div v-if="tab === 'overview'" class="card">
        <div class="card-title">项目概览</div>
        <div class="report-grid">
          <div class="report-item"><div class="label">类型</div><div class="value">{{ project.genre }}</div></div>
          <div class="report-item"><div class="label">状态</div><div class="value">{{ project.status === 'draft' ? '草稿' : project.status === 'active' ? '创作中' : '已完成' }}</div></div>
          <div class="report-item"><div class="label">分卷</div><div class="value">{{ volumes.length }}</div></div>
          <div class="report-item"><div class="label">角色</div><div class="value">{{ characters.length }}</div></div>
          <div class="report-item" v-if="project.word_goal"><div class="label">目标字数</div><div class="value">{{ (project.word_goal/10000).toFixed(1) }}万</div></div>
          <div class="report-item"><div class="label">已写字数</div><div class="value">{{ totalWordCount.toLocaleString() }} 字</div></div>
        </div>
        <div v-if="project.word_goal && wordGoalWarning" class="card" style="margin-top:12px;padding:12px;background:rgba(245,158,11,0.1);border-color:var(--yellow)">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:18px">⚠️</span>
            <div>
              <div style="font-weight:600;font-size:13px">字数预警</div>
              <div style="font-size:12px;color:var(--text-dim)">{{ wordGoalWarning }}</div>
              <div style="margin-top:4px;height:6px;background:var(--bg);border-radius:3px;overflow:hidden;max-width:400px">
                <div :style="{ width: wordGoalPercent + '%', height: '100%', background: wordGoalPercent > 90 ? 'var(--red)' : wordGoalPercent > 75 ? 'var(--yellow)' : 'var(--green)', borderRadius: '3px', transition: 'width 0.3s' }"></div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="project.core_theme" style="margin-top:12px;padding:12px;background:var(--bg);border-radius:var(--radius-sm)">
          <div class="text-dim" style="font-size:11px;margin-bottom:4px">💡 主控思想</div>
          <div style="font-size:14px;font-weight:600;color:var(--accent)">{{ project.core_theme }}</div>
        </div>
      </div>

      <!-- 大纲（三级体系） -->
      <div v-if="tab === 'outline'" class="card">
        <div style="margin-bottom:16px">
          <div class="card-title" style="margin-bottom:8px">📖 全书大纲</div>
          <div class="text-dim" style="font-size:11px;margin-bottom:4px">作为全书的灵魂线，为故事走向及人物塑造把控定下基调</div>
          <textarea v-model="bookOutlineText" rows="6"
            placeholder="描述全书的故事走向、核心冲突、人物成长主线"
            style="font-family:inherit;line-height:1.7"></textarea>
          <button class="btn btn-sm btn-primary" @click="saveBookOutline" style="margin-top:6px" :disabled="savingOutline">
            {{ savingOutline ? '保存中...' : '💾 保存全书大纲' }}
          </button>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:16px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span class="card-title" style="margin-bottom:0">📦 分卷大纲</span>
            <button class="btn btn-sm btn-primary" @click="showVolumeDialog = true">新建分卷</button>
          </div>
          <div class="text-dim" style="font-size:11px;margin-bottom:12px">负责整体故事的情节推动、上下文承接变化，保证逻辑与故事内核的稳定</div>

          <div v-for="(v, vi) in volumes" :key="v.id" class="volume-block">
            <div class="volume-header" @click="v._expanded = !v._expanded">
              <span class="volume-title">📦 第{{ v.vol_order }}卷· {{ v.title }}</span>
              <span class="text-dim" style="font-size:12px">{{ v.chapters?.length || 0 }} 章</span>
              <button class="btn btn-xs" style="margin-left:8px;color:var(--red);background:transparent;border:none;font-size:14px" @click.stop="handleDeleteVolume(v)" title="删除分卷">🗑</button>
              <span style="margin-left:auto;font-size:12px;color:var(--text-dim)">{{ v._expanded ? '▼' : '▶' }}</span>
            </div>
            <div v-if="v._expanded" style="padding:8px 0 0 12px">
              <div style="margin-bottom:8px">
                 <div class="text-dim" style="font-size:11px;margin-bottom:2px">分卷概述（情节推动、上下文承接）</div>
                <textarea v-model="v.summary" rows="2" style="font-size:12px;font-family:inherit" @change="updateVolumeOutline(v)"></textarea>
              </div>
              <div v-for="ch in v.chapters" :key="ch.id" class="chapter-item" @click="$router.push('/chapter/' + ch.id)">
                <span>{{ ch.chapter_order }}. {{ ch.title }}</span>
                <span class="tag" :class="'status-' + ch.status" style="font-size:10px">
                  {{ ch.status === 'draft' ? '草稿' : ch.status === 'writing' ? '写作中' : ch.status === 'review' || ch.status === 'reviewing' ? '审校中' : '已完成' }}
                </span>
                <button class="btn btn-xs" style="margin-left:auto;color:var(--red);background:transparent;border:none;font-size:12px" @click.stop="handleDeleteChapter(ch)" title="删除章节">✕</button>
              </div>
              <div style="margin-top:6px;padding:8px;background:var(--bg);border-radius:4px">
                <div class="text-dim" style="font-size:11px;margin-bottom:2px">章节大纲（具体内容构思）</div>
                 <div v-if="v.chapters.length === 0" class="text-dim" style="font-size:12px">暂无章节，添加章节后可在此编辑章节大纲</div>
                <div v-for="ch in v.chapters" :key="ch.id" style="margin-bottom:4px">
                  <div style="font-size:12px;font-weight:600">{{ ch.chapter_order }}. {{ ch.title }}</div>
                  <textarea v-model="ch.skeleton" rows="2" style="font-size:11px;font-family:inherit" :placeholder="'第' + ch.chapter_order + '章的内容构思...'" @change="updateChapterSkeleton(ch)"></textarea>
                </div>
              </div>
              <button class="btn btn-sm btn-outline" style="margin-top:6px;font-size:11px"
                 @click.stop="createChapter(v.id, v.chapters?.length || 0)">添加章节</button>
            </div>
          </div>
        </div>

        <div v-if="showVolumeDialog" class="modal-overlay" @click.self="showVolumeDialog = false">
          <div class="modal" style="max-width:400px">
            <h4 style="margin-bottom:12px">新建分卷</h4>
            <div class="form-group"><label>分卷名称</label><input v-model="volForm.title" /></div>
            <div class="form-group"><label>分卷序号</label><input v-model.number="volForm.vol_order" type="number" /></div>
            <div class="form-group"><label>分卷大纲</label><textarea v-model="volForm.outline" rows="3" placeholder="描述分卷的情节推动和上下文承接"></textarea></div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
              <button class="btn btn-outline btn-sm" @click="showVolumeDialog = false">取消</button>
              <button class="btn btn-primary btn-sm" @click="handleCreateVolume">创建</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 角色（八维塑造） -->
      <div v-if="tab === 'characters'" class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <span class="card-title" style="margin-bottom:0">👤 角色管理</span>
          <button class="btn btn-sm btn-primary" @click="showCharDialog = true">添加角色</button>
        </div>
        <div v-if="characters.length === 0" class="empty-state" style="padding:20px">
          <div class="desc">还没有角色，创建主要角色开始创作</div>
        </div>
        <div class="char-grid">
          <div v-for="c in characters" :key="c.id" class="char-card" @click="openCharEdit(c)" style="cursor:pointer">
            <div style="display:flex;align-items:center;gap:8px">
              <div class="char-name">{{ c.name }}</div>
              <button class="btn btn-xs" style="margin-left:auto;color:var(--red);background:transparent;border:none;font-size:14px" @click.stop="handleDeleteCharacter(c)" title="删除角色">🗑</button>
            </div>
            <span class="tag" :class="'role-' + c.role">{{ c.role }}</span>
            <div class="char-dims">
              <div v-if="c.gender" class="dim-item"><span class="dim-label">性别</span><span>{{ c.gender }}</span></div>
              <div v-if="c.age" class="dim-item"><span class="dim-label">年龄</span><span>{{ c.age }}</span></div>
              <div v-if="c.personality" class="dim-item"><span class="dim-label">性格</span><span>{{ c.personality }}</span></div>
              <div v-if="c.family_background" class="dim-item"><span class="dim-label">家庭背景</span><span>{{ c.family_background }}</span></div>
              <div v-if="c.occupation" class="dim-item"><span class="dim-label">职业</span><span>{{ c.occupation }}</span></div>
              <div v-if="c.values" class="dim-item"><span class="dim-label">价值观</span><span>{{ c.values }}</span></div>
              <div v-if="c.special_traits" class="dim-item"><span class="dim-label">特殊癖好/习惯</span><span>{{ c.special_traits }}</span></div>
              <div class="dim-item">
                <span class="dim-label">状态</span>
                <span :style="{color: c.character_status === 'active' ? 'var(--green)' : c.character_status === 'foreshadow' ? 'var(--yellow)' : 'var(--red)'}">
                  {{ project.status === 'active' ? '暂停' : '开始创作' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="showCharDialog" class="modal-overlay" @click.self="showCharDialog = false; editingChar = null">
          <div class="modal" style="max-width:600px">
            <h4 style="margin-bottom:16px">{{ editingChar ? '编辑角色' : '添加角色' }} · 八维塑造</h4>
            <div class="form-row">
              <div class="form-group" style="flex:2"><label>角色名称 *</label><input v-model="charForm.name" /></div>
              <div class="form-group" style="flex:1"><label>角色定位</label>
                 <select v-model="charForm.role"><option>主角</option><option>配角</option><option>反派</option><option>其他</option></select></div>
            </div>
            <div class="form-row">
              <div class="form-group" style="flex:1"><label>性别</label>
                <select v-model="charForm.gender"><option value="">未设置</option><option>男</option><option>女</option><option>其他</option></select></div>
              <div class="form-group" style="flex:1"><label>年龄</label><input v-model="charForm.age" placeholder="如：18岁 / 青年" /></div>
              <div class="form-group" style="flex:1"><label>职业</label><input v-model="charForm.occupation" placeholder="如：研究员" /></div>
            </div>
            <div class="form-row">
              <div class="form-group" style="flex:1"><label>性格</label><textarea v-model="charForm.personality" rows="2" placeholder="性格特征描述"></textarea></div>
              <div class="form-group" style="flex:1"><label>家庭背景</label><textarea v-model="charForm.family_background" rows="2" placeholder="出身、家庭关系等"></textarea></div>
            </div>
            <div class="form-row">
              <div class="form-group" style="flex:1"><label>价值观</label><textarea v-model="charForm.values" rows="2" placeholder="信念、追求、底线等"></textarea></div>
              <div class="form-group" style="flex:1"><label>特殊癖好/习惯</label><textarea v-model="charForm.special_traits" rows="2" placeholder="口头禅、小动作、习惯等"></textarea></div>
            </div>
              <div class="form-group">
              <label>状态</label>
              <select v-model="charForm.character_status">
                <option value="active">👤 活跃（在线）</option>
                <option value="foreshadow">🔮 伏笔中（有伏笔待回收）</option>
                <option value="offline">💤 已下线</option>
              </select>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
              <button class="btn btn-outline btn-sm" @click="showCharDialog = false">取消</button>
              <button class="btn btn-primary btn-sm" @click="handleCreateCharacter" :disabled="!charForm.name">{{ editingChar ? '保存修改' : '添加角色' }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 章节 -->
      <div v-if="tab === 'chapters'" class="card">
        <div class="card-title">📝 所有章节</div>
        <div v-if="allChapters.length === 0" class="empty-state" style="padding:20px">
          <div class="desc">先在大纲中创建分卷和章节</div>
        </div>
        <div v-for="ch in allChapters" :key="ch.id" class="chapter-item" @click="$router.push('/chapter/' + ch.id)">
          <span>{{ ch.chapter_order }}. {{ ch.title }}</span>
          <span style="margin-left:auto;font-size:12px;color:var(--text-dim)">卷{{ ch.volume_id }}</span>
          <span class="tag" :class="'status-' + ch.status" style="margin-left:8px">
            {{ ch.status === 'draft' ? '草稿' : ch.status === 'writing' ? '写作中' : ch.status === 'review' || ch.status === 'reviewing' ? '审校中' : '已完成' }}
          </span>
          <span style="margin-left:8px;font-size:11px;color:var(--text-dim)">v{{ ch.version }}</span>
          <span style="margin-left:8px;font-size:11px;color:var(--text-dim)">{{ (ch.content?.length || 0).toLocaleString() }}</span>
          <button class="btn btn-xs" style="color:var(--red);background:transparent;border:none;font-size:14px" @click.stop="handleDeleteChapter(ch)" title="删除章节">🗑</button>
        </div>
      </div>

      <!-- 世界观 -->
      <div v-if="tab === 'world'" class="card">
        <div class="card-title">🌍 世界观建设</div>
        <textarea v-model="worldText" rows="15" style="font-family:inherit;line-height:1.7"
          placeholder="描述你的世界观：世界规则、力量体系、地理、历史、势力分布"
          @input="autoSaveWorld"></textarea>
        <div style="display:flex;gap:8px;align-items:center;margin-top:8px">
          <button class="btn btn-primary btn-sm" @click="saveWorld" :disabled="savingWorld">
            {{ savingWorld ? '保存中...' : '💾 保存世界观' }}
          </button>
          <span v-if="worldSaved" style="font-size:11px;color:var(--green)">已自动保存</span>
          <span v-else style="font-size:11px;color:var(--text-dim)">输入停止后自动保存</span>
        </div>
      </div>

      <!-- Agent 对话面板（分区助理） -->
      <div class="card" style="margin-top:12px;border:1px solid rgba(245,158,11,0.2)">
        <div class="card-title" style="display:flex;justify-content:space-between;align-items:center">
          <span>💬 {{ tab === 'world' ? '🌍世界观' : tab === 'outline' ? '📋大纲' : tab === 'characters' ? '👤角色' : tab === 'chapters' ? '📝章节' : '💬综合' }} · Agent 对话</span>
          <div style="display:flex;gap:4px">
            <button v-for="t in agentTypes" :key="t.key" class="btn btn-xs" :class="chatAgent === t.key ? 'btn-primary' : 'btn-outline'"
              @click="chatAgent = t.key; loadChat()">{{ t.icon }} {{ t.label }}</button>
            <button class="btn btn-xs btn-outline" style="color:var(--red)" @click="clearCurrentChat" title="清除本区对话">🗑</button>
          </div>
        </div>
        <div class="chat-box" ref="chatBox">
          <div v-for="msg in chatMessages" :key="msg.id" class="chat-msg" :class="msg.role">
            <div class="chat-avatar">{{ msg.role === 'user' ? '你' : (msg.agent_type === 'creator' ? '创作者' : msg.agent_type === 'supervisor' ? '督查者' : '读者') }}</div>
            <div class="chat-bubble">
              <div class="chat-bubble-header">
                <span style="font-size:11px;color:var(--text-dim)">{{ msg.role === 'user' ? '你' : (msg.agent_type === 'creator' ? '创作者' : msg.agent_type === 'supervisor' ? '督查者' : '读者') }}</span>
                <div style="display:flex;gap:2px">
                  <button class="copy-btn" @click="copyText(msg.content)" title="复制内容">📋</button>
                </div>
              </div>
              <div style="white-space:pre-wrap;font-size:13px;line-height:1.6">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="chatLoading" class="chat-msg agent">
            <div class="chat-avatar">{{ chatAgentIcon(chatAgent) }}</div>
            <div class="chat-bubble">
              <div style="font-size:10px;color:var(--text-dim);margin-bottom:4px">AI 正在思考...</div>
              <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
          </div>
          <div v-if="chatMessages.length === 0 && !chatLoading" style="text-align:center;padding:24px;color:var(--text-dim);font-size:13px">
            开启 Agent 对话，用 AI 辅助构建世界观、角色设定、大纲思路、故事走向<br>
            <span style="font-size:12px">            💡 当前为 {{ tab === 'world' ? '🌍世界观' : tab === 'outline' ? '📋大纲' : tab === 'characters' ? '👤角色' : tab === 'chapters' ? '📝章节' : '📖综合' }} 模式，对话将针对该区域生成内容</span>
          </div>
        </div>
        <div class="chat-input-row">
          <span class="chat-mode-tag" :class="'mode-' + tab">{{ tab === 'world' ? '🌍' : tab === 'outline' ? '📋' : tab === 'characters' ? '👤' : tab === 'chapters' ? '📝' : '💬' }} {{ tab === 'world' ? '世界观' : tab === 'outline' ? '大纲' : tab === 'characters' ? '角色' : tab === 'chapters' ? '章节' : '综合' }}</span>
          <textarea v-model="chatInput" rows="2" :disabled="chatLoading" placeholder="输入创作需求..." @keydown.enter="sendChat"></textarea>
          <button class="btn btn-primary" @click="sendChat" :disabled="!chatInput.trim() || chatLoading" style="align-self:flex-end;white-space:nowrap">发送</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, watch, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useApi } from '../api'

export default {
  name: 'ProjectDetail',
  setup() {
    const route = useRoute()
    const api = useApi()
    const project = ref(null)
    const loadError = ref('')
    const volumes = ref([])
    const characters = ref([])
    const tab = ref('overview')
    const savingWorld = ref(false)
    const savingOutline = ref(false)

    const showVolumeDialog = ref(false)
    const volForm = ref({ title: '', vol_order: 1, summary: '', outline: '' })
    const showCharDialog = ref(false)
    const editingChar = ref(null)
    const charForm = ref({
      name: '', role: '配角', gender: '', age: '', personality: '',
      family_background: '', occupation: '', values: '', special_traits: '',
      character_status: 'active'
    })

    const allChapters = computed(() => {
      const chs = []
      for (const v of volumes.value) {
        if (v.chapters) {
          for (const ch of v.chapters) {
            chs.push({ ...ch, volume_id: v.id })
          }
        }
      }
      return chs.sort((a, b) => a.chapter_order - b.chapter_order)
    })

    const totalWordCount = computed(() => {
      let total = 0
      for (const ch of allChapters.value) {
        if (ch.content) {
          total += ch.content.replace(/\s/g, '').length
        }
      }
      return total
    })

    const wordGoalPercent = computed(() => {
      if (!project.value?.word_goal || project.value.word_goal === 0) return 0
      return Math.min(100, Math.round((totalWordCount.value / project.value.word_goal) * 100))
    })

    const wordGoalWarning = computed(() => {
      if (!project.value?.word_goal) return ''
      const pct = wordGoalPercent.value
      if (pct >= 100) return `已超出目标字数！目标：${project.value.word_goal.toLocaleString()} 字，已写：${totalWordCount.value.toLocaleString()} 字（${pct}%）`
      if (pct >= 90) return `接近目标字数上限！目标：${project.value.word_goal.toLocaleString()} 字，已写：${totalWordCount.value.toLocaleString()} 字（${pct}%），建议精简后续章节`
      if (pct >= 75) return `已写 ${totalWordCount.value.toLocaleString()} 字，达到目标 ${project.value.word_goal.toLocaleString()} 字的 ${pct}%`
      return ''
    })

    const bookOutlineText = computed({
      get: () => project.value?.whole_book_outline || '',
      set: (v) => { if (project.value) project.value.whole_book_outline = v }
    })

    const worldText = computed({
      get: () => {
        if (!project.value?.world_setting) return ''
        if (typeof project.value.world_setting === 'string') return project.value.world_setting
        return JSON.stringify(project.value.world_setting, null, 2)
      },
      set: (v) => { if (project.value) project.value.world_setting = v }
    })

    // Auto-save state
    const worldSaved = ref(false)
    const outlineSaved = ref(false)
    let autoSaveWorldTimer = null
    let autoSaveOutlineTimer = null
    let lastSavedWorld = ''
    let lastSavedOutline = ''

    function autoSaveWorld() {
      worldSaved.value = false
      if (autoSaveWorldTimer) clearTimeout(autoSaveWorldTimer)
      autoSaveWorldTimer = setTimeout(async () => {
        await saveWorld()
        worldSaved.value = true
      }, 5000)
    }
    function autoSaveOutline() {
      outlineSaved.value = false
      if (autoSaveOutlineTimer) clearTimeout(autoSaveOutlineTimer)
      autoSaveOutlineTimer = setTimeout(async () => {
        await saveBookOutline()
        outlineSaved.value = true
      }, 5000)
    }

    async function loadProject() {
      loadError.value = ''
      console.log('Loading project:', route.params.id)
      try {
        const res = await api.getProject(route.params.id)
        if (!res.data || !res.data.id) {
          throw new Error('项目不存在 (ID: ' + route.params.id + ')')
        }
        project.value = res.data
        const volsRes = await api.getVolumes(route.params.id)
        volumes.value = (volsRes.data || []).map(v => ({ ...v, _expanded: false }))
        const charsRes = await api.getCharacters(route.params.id)
        characters.value = charsRes.data || []
      } catch (e) {
        console.error('loadProject error:', e)
        loadError.value = e.response?.data?.detail || e.message || '加载失败'
      }
    }

    async function handleCreateVolume() {
      // 字数预设校验
      if (project.value?.word_goal && wordGoalPercent.value >= 90) {
        if (!confirm(`⚠️ 当前已写字数达目标字数的 ${wordGoalPercent.value}%。确定继续新建分卷吗？`)) return
      }
      await api.createVolume(project.value.id, volForm.value)
      showVolumeDialog.value = false
      volForm.value = { title: '', vol_order: volumes.value.length + 1, summary: '', outline: '' }
      await loadProject()
    }

    async function updateVolumeOutline(v) {
      await api.updateVolume?.(v.id, { summary: v.summary }) || await api.updateProject(project.value.id, {})
    }

    async function updateChapterSkeleton(ch) {
      await api.updateChapter(ch.id, { skeleton: ch.skeleton })
    }

    function openCharEdit(c) {
      editingChar.value = c
      charForm.value = {
        name: c.name, role: c.role, gender: c.gender || '', age: c.age || '',
        personality: c.personality || '', family_background: c.family_background || '',
        occupation: c.occupation || '', values: c.values || '',
        special_traits: c.special_traits || '', character_status: c.character_status || 'active'
      }
      showCharDialog.value = true
    }

    async function handleCreateCharacter() {
      const data = { ...charForm.value }
      if (editingChar.value) {
        await api.updateCharacter(project.value.id, editingChar.value.id, data)
      } else {
        await api.createCharacter(project.value.id, data)
      }
      showCharDialog.value = false
      editingChar.value = null
      charForm.value = { name: '', role: '配角', gender: '', age: '', personality: '',
        family_background: '', occupation: '', values: '', special_traits: '', character_status: 'active' }
      await loadProject()
    }

    async function handleDeleteCharacter(c) {
      if (!confirm(`确定删除角色「${c.name}」吗？`)) return
      await api.deleteCharacter(project.value.id, c.id)
      await loadProject()
      showToast('已删除角色')
    }

    async function handleDeleteVolume(v) {
      if (!confirm(`确定删除分卷「${v.title}」及其下所有章节吗？`)) return
      await api.deleteVolume(v.id)
      await loadProject()
      showToast('已删除分卷')
    }

    async function handleDeleteChapter(ch) {
      if (!confirm(`确定删除章节「${ch.title}」吗？`)) return
      await api.deleteChapter(ch.id)
      await loadProject()
      showToast('已删除章节')
    }

    async function createChapter(vid, order) {
      // 字数预设校验
      if (project.value?.word_goal && wordGoalPercent.value >= 90) {
        if (!confirm(`⚠️ 当前已写字数达目标字数的 ${wordGoalPercent.value}%。确定继续新建章节吗？`)) return
      }
      await api.createChapter(vid, { title: `第${order + 1}章`, chapter_order: order + 1 })
      await loadProject()
    }

    async function toggleStatus() {
      const newStatus = project.value.status === 'active' ? 'draft' : 'active'
      await api.updateProject(project.value.id, { status: newStatus })
      project.value.status = newStatus
    }

    async function saveWorld() {
      savingWorld.value = true
      try {
        await api.updateProject(project.value.id, { world_setting: project.value.world_setting })
      } finally { savingWorld.value = false }
    }

    async function saveBookOutline() {
      savingOutline.value = true
      try {
        await api.updateProject(project.value.id, { whole_book_outline: bookOutlineText.value })
      } finally { savingOutline.value = false }
    }

    // Chat system
    const chatMessages = ref([])
    const chatInput = ref('')
    const chatLoading = ref(false)
    const chatAgent = ref('creator')
    const chatBox = ref(null)
    const toastMsg = ref('')
    const toastVisible = ref(false)
    let toastTimer = null
    function showToast(msg) {
      toastMsg.value = msg
      toastVisible.value = true
      if (toastTimer) clearTimeout(toastTimer)
      toastTimer = setTimeout(() => { toastVisible.value = false }, 4000)
    }
    const agentTypes = [
      { key: 'creator', label: '创作者', icon: '✍️' },
      { key: 'supervisor', label: '督查者', icon: '🔍' },
      { key: 'reader', label: '读者', icon: '📚' },
    ]

    function chatAgentIcon(type) {
      return { creator: '✍️', supervisor: '🔍', reader: '📚' }[type] || '❓'
    }

    async function loadChat() {
      if (!project.value) return
      try {
        const res = await api.getChatMessages(project.value.id, chatAgent.value, tab.value)
        chatMessages.value = res.data || []
        await nextTick()
        if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
      } catch(e) {}
    }

    async function sendChat() {
      const msg = chatInput.value.trim()
      if (!msg || chatLoading.value || !project.value) return
      chatInput.value = ''
      chatLoading.value = true
      try {
        const res = await api.sendChatMessage(project.value.id, {
          agent_type: chatAgent.value,
          message: msg,
          section: tab.value  // 传递当前编辑区域
        })
        if (res.data) {
          chatMessages.value.push({ id: Date.now(), role: 'user', agent_type: chatAgent.value, content: msg })
          const replyContent = res.data.agent_reply?.content || '（无回应）'
          chatMessages.value.push({ id: Date.now() + 1, role: 'agent', agent_type: chatAgent.value, content: replyContent })
          
          // 自动同步大纲类对话内容到分卷大纲
          if (tab.value === 'outline' && chatAgent.value === 'creator' && volumes.value.length > 0) {
            // 将对话内容同步到最后更新的分卷大纲中
            const lastVolume = volumes.value[volumes.value.length - 1]
            if (lastVolume) {
              try {
                const newOutline = (lastVolume.outline || '') + '\n\n【Agent对话同步】' + replyContent.substring(0, 500)
                await api.updateVolume(lastVolume.id, { outline: newOutline })
                lastVolume.outline = newOutline
                showToast('📋 对话内容已同步到分卷大纲')
              } catch(e) { /* ignore sync errors */ }
            }
          }

          // 如果有自动同步的动作，刷新项目数据并提示
          const actions = res.data.agent_reply?.auto_actions
          if (actions && actions.length > 0) {
            // 重新加载项目更新数据
            await loadProject()
            // 显示通知
            const labels = actions.map(a => a.label).join('; ')
            showToast('✅ ' + labels)
          } else {
            const section = res.data.agent_reply?.section
            if (section && section !== 'general' && section !== 'chapters') {
              showToast('💡 检测到结构化内容，将自动复制相关文本到对应区域')
            }
          }
          
          await nextTick()
          if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
        }
      } catch(e) {
        chatMessages.value.push({ id: Date.now(), role: 'agent', agent_type: chatAgent.value, content: '⚠️ 发送失败' })
      } finally { chatLoading.value = false }
    }

    function copyText(text) {
      navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板')
      }).catch(() => {
        // fallback
        const ta = document.createElement('textarea')
        ta.value = text
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      })
    }

    async function syncMessage(msg) {
      if (!project.value || msg.role !== 'agent') return
      try {
        const res = await api.syncChatMessage(project.value.id, msg.id, {
          section: tab.value,
          target: msg.content.substring(0, 10) + '...',
        })
        showToast('🔗 ' + (res.data?.detail || '已同步'))
        await loadProject()
        await loadChat()
      } catch (e) {
        showToast('⚠️ 同步失败: ' + (e.message || ''))
      }
    }

    async function clearCurrentChat() {
      if (!project.value) return
      if (!confirm('确定清除当前区域的对话历史吗？')) return
      try {
        await api.clearChatHistory(project.value.id, null, tab.value)
        chatMessages.value = []
        showToast('🗑️ 对话历史已清除')
      } catch (e) {
        showToast('⚠️ 清除失败')
      }
    }


    const loadData = async () => {
      loadError.value = ''
      try {
        await loadProject()
      } catch (e) {
        console.error('Failed to load project:', e)
        if (!loadError.value) loadError.value = '加载项目发生错误 ' + (e.message || '未知错误')
      }
      try {
        await loadChat()
      } catch (e) {
        // Chat is optional
      }
    }

    onMounted(async () => {
      await loadData()
    })

    // Retry when route params change (project ID in URL)
    watch(() => route.params.id, () => {
      project.value = null
      loadData()
    })

    return {
      project, volumes, characters, tab, allChapters, totalWordCount, wordGoalWarning, wordGoalPercent, worldText, savingWorld, savingOutline, worldSaved, outlineSaved, autoSaveWorld, autoSaveOutline,
      bookOutlineText, showVolumeDialog, volForm, showCharDialog, charForm, editingChar,
      handleCreateVolume, updateVolumeOutline, updateChapterSkeleton,
      handleCreateCharacter, handleDeleteCharacter, handleDeleteVolume, handleDeleteChapter,
      openCharEdit, createChapter, toggleStatus, saveWorld, saveBookOutline,
      chatMessages, chatInput, chatLoading, chatAgent, chatBox, agentTypes,
      loadChat, sendChat, chatAgentIcon, copyText, loadError,
      syncMessage, clearCurrentChat,
      toastMsg, toastVisible
    }
  }
}
</script>

<style scoped>
.tabs { display: flex; gap: 2px; margin-bottom: 16px; background: var(--bg-card); border-radius: var(--radius); padding: 4px; border: 1px solid var(--border); }
.tab { padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; transition: all 0.2s; }
.tab:hover { background: var(--bg-hover); }
.tab.active { background: rgba(245,158,11,0.12); color: var(--accent); font-weight: 600; }
.volume-block { margin-bottom: 8px; border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.volume-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; background: var(--bg); }
.volume-header:hover { background: var(--bg-hover); }
.volume-title { font-size: 14px; font-weight: 600; }
.chapter-item { display: flex; align-items: center; gap: 8px; padding: 6px 10px; cursor: pointer; border-radius: 4px; font-size: 13px; }
.chapter-item:hover { background: var(--bg-hover); }
.char-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px; }
.char-card { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; }
.char-name { font-size: 16px; font-weight: 700; margin-bottom: 4px; display: inline-block; margin-right: 8px; }
.char-dims { margin-top: 8px; }
.dim-item { display: flex; gap: 8px; padding: 3px 0; font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.dim-item:last-child { border-bottom: none; }
.dim-label { color: var(--text-dim); min-width: 80px; flex-shrink: 0; }
.role-主角 { background: rgba(245,158,11,0.15); color: var(--accent); }
.role-配角 { background: rgba(59,130,246,0.15); color: var(--blue); }
.role-反派 { background: rgba(239,68,68,0.15); color: var(--red); }
.role-其他 { background: rgba(234,179,8,0.15); color: var(--yellow); }
.tag { display:inline-block; padding:1px 6px; border-radius:8px; font-size:11px; font-weight:600; }
.status-draft { background: rgba(234,179,8,0.15); color: var(--yellow); }
.status-writing { background: rgba(59,130,246,0.15); color: var(--blue); }
.status-review, .status-reviewing { background: rgba(139,92,246,0.15); color: #a78bfa; }
.status-approved { background: rgba(34,197,94,0.15); color: var(--green); }
.status-active { background: rgba(34,197,94,0.15); color: var(--green); }
textarea { width: 100%; border: 1px solid var(--border); background: var(--bg); color: var(--text); border-radius: var(--radius-sm); padding: 8px; resize: vertical; }
textarea:focus { outline: none; border-color: var(--accent); }

/* Chat styles */
.chat-box { max-height:400px; overflow-y:auto; padding:12px; background:var(--bg); border-radius:var(--radius-sm); margin:8px 0; }
.chat-msg { display:flex; gap:8px; margin-bottom:12px; }
.chat-msg.user { flex-direction:row-reverse; }
.chat-avatar { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:16px; background:var(--bg-card); flex-shrink:0; }
.chat-bubble { max-width:80%; padding:10px 14px; border-radius:12px; background:var(--bg-card); border:1px solid var(--border); }
.chat-msg.user .chat-bubble { background:rgba(245,158,11,0.08); border-color:rgba(245,158,11,0.2); }
.chat-input-row { display:flex; gap:8px; align-items:flex-end; }
.chat-input-row textarea { flex:1; border:1px solid var(--border); background:var(--bg); color:var(--text); border-radius:var(--radius-sm); padding:8px; font-family:inherit; font-size:13px; resize:vertical; min-height:44px; }
.chat-input-row textarea:focus { outline:none; border-color:var(--accent); }
.typing-indicator { display:flex; gap:4px; padding:8px 0; }
.typing-indicator span { width:6px; height:6px; border-radius:50%; background:var(--text-dim); animation:typing 1s infinite; }
.typing-indicator span:nth-child(2) { animation-delay:0.2s; }
.typing-indicator span:nth-child(3) { animation-delay:0.4s; }
@keyframes typing { 0%,60%,100% { opacity:0.3; transform:translateY(0); } 30% { opacity:1; transform:translateY(-4px); } }
</style>

