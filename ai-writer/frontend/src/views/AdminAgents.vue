<template>
  <div>
    <div class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px">
      <span style="font-size:16px;font-weight:700">⚙️ Agent 管理中心</span>
      <span class="text-dim" style="font-size:12px">在这里配置创作者、督查者、读者的人设和能力</span>
      <button class="btn btn-primary btn-sm" @click="showCreate = true" style="margin-left:auto">➕ 新建 Agent</button>
      <button class="btn btn-sm btn-outline" @click="showGenerateDialog = true" style="color:var(--accent)">🤖 对话配置</button>
      <button class="btn btn-sm btn-outline" style="color:var(--red)" @click="deleteAllAgents">🗑️ 清空全部</button>
    </div>

    <!-- Agent 配置列表 -->
    <div class="card" v-for="agent in agents" :key="agent.id" style="position:relative">
      <button class="delete-btn" @click="deleteAgent(agent)" title="删除此 Agent">✕</button>
      <div class="agent-header">
        <div>
          <span class="agent-icon">{{ agentIcon(agent.agent_type) }}</span>
          <span class="agent-name">{{ agent.name }}</span>
          <span class="tag" :class="agent.agent_type">
            {{ agent.agent_type === 'creator' ? '创作者' : agent.agent_type === 'supervisor' ? '督查者' : '读者' }}
          </span>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <span class="status-dot" :class="agent.is_active ? 'on' : 'off'"></span>
          <span style="font-size:12px;color:var(--text-dim)">{{ agent.is_active ? '已启用' : '已停用' }}</span>
          <button class="btn btn-sm btn-outline" @click="editAgent(agent)">✏️ 编辑</button>
          <button class="btn btn-sm" :class="agent.is_active ? 'btn-outline' : 'btn-primary'"
            style="font-size:11px" @click="toggleActive(agent)">
            {{ agent.is_active ? '停用' : '启用' }}
          </button>
        </div>
      </div>

      <div class="agent-section">
        <div class="section-label">🧠 系统提示词（人设 + 核心能力）</div>
        <div class="prompt-preview">{{ agent.system_prompt?.substring(0, 200) || '（未配置）' }}{{ (agent.system_prompt?.length || 0) > 200 ? '…' : '' }}</div>
      </div>

      <div class="agent-section">
        <div class="section-label">⚡ 能力列表</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">
          <span v-if="!agent.capabilities?.length" class="text-dim" style="font-size:12px">（未配置）</span>
          <span v-for="cap in agent.capabilities" :key="cap"
            class="cap-tag">{{ cap }}</span>
        </div>
      </div>

      <div class="agent-section" style="border:none;margin-bottom:0;padding-bottom:0">
        <div class="section-label">⚙️ 模型参数</div>
        <div style="font-size:12px;color:var(--text-dim);display:flex;gap:16px;margin-top:4px">
          <span>模型: {{ agent.model }}</span>
          <span v-if="agent.parameters?.temperature">Temperature: {{ agent.parameters.temperature }}</span>
          <span v-if="agent.parameters?.max_tokens">Max Tokens: {{ agent.parameters.max_tokens }}</span>
        </div>
      </div>

      <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
        <div class="section-label">🧪 测试</div>
        <div style="display:flex;gap:8px;margin-top:6px">
          <input v-model="testInputs[agent.id]" placeholder="输入测试消息..." style="flex:1;font-size:12px" />
          <button class="btn btn-sm btn-outline" @click="testAgent(agent)" :disabled="testing[agent.id]">
            {{ testing[agent.id] ? '测试中...' : '发送测试' }}
          </button>
        </div>
        <div v-if="testResults[agent.id]" style="margin-top:6px;font-size:12px;color:var(--text-dim);padding:8px;background:var(--bg);border-radius:4px">
          {{ testResults[agent.id] }}
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!agents.length && !loading" class="empty-state">
      <div class="icon">🤖</div>
      <div class="title">还没有 Agent 配置</div>
      <div class="desc">创建创作者、督查者、读者三个 Agent，配置他们的人设和能力</div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <!-- 对话配置弹窗 -->
    <div v-if="showGenerateDialog" class="modal-overlay" @click.self="showGenerateDialog = false">
      <div class="modal" style="max-width:560px">
        <h4 style="margin-bottom:16px">🤖 通过对话配置 Agent</h4>
        <p style="font-size:12px;color:var(--text-dim);margin-bottom:12px">
          用自然语言描述你需要的 Agent 类型、人设和能力，系统将自动生成配置并填入编辑表单。
        </p>
        <div class="form-group">
          <label>需求描述</label>
          <textarea v-model="generateDescription" rows="6" placeholder="例如：我需要一个严肃的历史小说督查者，重点关注史实准确性、人物性格一致性、情节逻辑自洽，输出格式为结构化评审报告..."></textarea>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn btn-outline btn-sm" @click="showGenerateDialog = false">取消</button>
          <button class="btn btn-primary btn-sm" @click="handleGenerate" :disabled="generating || !generateDescription">
            {{ generating ? '生成中...' : '生成配置' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <div v-if="showCreate || editing" class="modal-overlay" @click.self="closeDialog">
      <div class="modal" style="max-width:600px">
        <h4 style="margin-bottom:16px">{{ editing ? '✏️ 编辑 Agent' : '➕ 新建 Agent' }}</h4>

        <div class="form-group">
          <label>Agent 类型</label>
          <select v-model="editForm.agent_type" :disabled="!!editing">
            <option value="creator">✍️ 创作者</option>
            <option value="supervisor">🔎 督查者</option>
            <option value="reader">📚 读者</option>
          </select>
        </div>

        <div class="form-group">
          <label>名称</label>
          <input v-model="editForm.name" placeholder="如：沈寒 / 明镜 / 言灵" />
        </div>

        <div class="form-group">
          <label>🧠 系统提示词（人设 + 核心能力描述）</label>
          <div class="text-dim" style="font-size:11px;margin-bottom:4px">
            这里配置 Agent 的人格、专业能力、行为规则、输出格式要求等。
            创作者：写作风格、世界观处理方法、人物塑造规则<br>
            督查者：检查标准、评分规则、反馈格式<br>
            读者：阅读偏好、评分维度、评论风格
          </div>
          <textarea v-model="editForm.system_prompt" rows="8"
            placeholder="在此编写 Agent 的人设和能力描述…"></textarea>
        </div>

        <div class="form-group">
          <label>能力列表（每行一个）</label>
          <textarea v-model="editForm.capabilitiesText" rows="3"
            placeholder="如：&#10;世界观构建&#10;角色弧光设计&#10;对话节奏控制"></textarea>
        </div>

        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label>模型</label>
            <input v-model="editForm.model" placeholder="deepseek-v4-flash" />
          </div>
          <div class="form-group" style="flex:1">
            <label>Temperature</label>
            <input v-model.number="editForm.temperature" type="number" step="0.1" min="0" max="2" placeholder="0.7" />
          </div>
          <div class="form-group" style="flex:1">
            <label>Max Tokens</label>
            <input v-model.number="editForm.max_tokens" type="number" placeholder="4096" />
          </div>
        </div>

        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
          <button class="btn btn-outline btn-sm" @click="closeDialog">取消</button>
          <button class="btn btn-primary btn-sm" @click="saveAgent">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useApi } from '../api'

export default {
  name: 'AdminAgents',
  setup() {
    const { getAgentConfigs, createAgentConfig, updateAgentConfig, deleteAgentConfig, deleteAllAgentConfigs, testAgent: apiTest, generateAgentConfig } = useApi()
    const agents = ref([])
    const loading = ref(true)
    const showCreate = ref(false)
    const editing = ref(null)
    const editForm = ref(emptyForm())
    const testInputs = ref({})
    const testResults = ref({})
    const testing = ref({})
    const showGenerateDialog = ref(false)
    const generateDescription = ref('')
    const generating = ref(false)

    function emptyForm() {
      return {
        agent_type: 'creator',
        name: '',
        system_prompt: '',
        model: 'deepseek-v4-flash',
        temperature: 0.7,
        max_tokens: 4096,
        capabilitiesText: ''
      }
    }

    function agentIcon(type) {
      const icons = { creator: '✍️', supervisor: '🔎', reader: '📚' }
      return icons[type] || '🤖'
    }

    function statusClass(status) {
      return 'status-' + status
    }

    async function loadAgents() {
      loading.value = true
      try {
        const res = await getAgentConfigs()
        agents.value = res.data || []
      } finally {
        loading.value = false
      }
    }

    function editAgent(agent) {
      editing.value = agent.id
      editForm.value = {
        agent_type: agent.agent_type,
        name: agent.name,
        system_prompt: agent.system_prompt || '',
        model: agent.model || 'deepseek-v4-flash',
        temperature: agent.parameters?.temperature || 0.7,
        max_tokens: agent.parameters?.max_tokens || 4096,
        capabilitiesText: (agent.capabilities || []).join('\n')
      }
    }

    function closeDialog() {
      showCreate.value = false
      editing.value = null
      editForm.value = emptyForm()
    }

    async function saveAgent() {
      const data = {
        name: editForm.value.name,
        agent_type: editForm.value.agent_type,
        system_prompt: editForm.value.system_prompt,
        model: editForm.value.model,
        parameters: {
          temperature: editForm.value.temperature,
          max_tokens: editForm.value.max_tokens
        },
        capabilities: editForm.value.capabilitiesText.split('\n').filter(Boolean)
      }

      if (editing.value) {
        await updateAgentConfig(editing.value, data)
      } else {
        await createAgentConfig(data)
      }

      closeDialog()
      await loadAgents()
    }

    async function toggleActive(agent) {
      await updateAgentConfig(agent.id, { is_active: !agent.is_active })
      await loadAgents()
    }

    async function testAgent(agent) {
      const input = testInputs.value[agent.id]
      if (!input) return
      testing.value[agent.id] = true
      try {
        const res = await apiTest(agent.id, { agent_type: agent.agent_type, chapter_id: 0, context: { project_id: 0, message: input } })
        testResults.value[agent.id] = res.data?.result || JSON.stringify(res.data)
      } catch (e) {
        testResults.value[agent.id] = '测试失败: ' + e.message
      } finally {
        testing.value[agent.id] = false
      }
    }

    async function deleteAgent(agent) {
      if (!confirm(`确定删除 Agent「${agent.name}」吗？`)) return
      await deleteAgentConfig(agent.id)
      await loadAgents()
    }

    async function deleteAllAgents() {
      if (!confirm('确定清空所有 Agent 配置吗？此操作不可撤销。')) return
      await deleteAllAgentConfigs()
      await loadAgents()
    }

    async function handleGenerate() {
      generating.value = true
      try {
        const res = await generateAgentConfig({ description: generateDescription.value })
        const config = res.data
        editForm.value = {
          agent_type: config.agent_type || 'creator',
          name: config.name || '',
          system_prompt: config.system_prompt || '',
          model: config.model || 'deepseek-v4-flash',
          temperature: config.parameters?.temperature ?? 0.7,
          max_tokens: config.parameters?.max_tokens ?? 4096,
          capabilitiesText: (config.capabilities || []).join('\n')
        }
        showGenerateDialog.value = false
        showCreate.value = true
        generateDescription.value = ''
      } catch (e) {
        alert('生成失败: ' + e.message)
      } finally {
        generating.value = false
      }
    }

    onMounted(loadAgents)

    return {
      agents, loading, showCreate, editing, editForm,
      testInputs, testResults, testing,
      showGenerateDialog, generateDescription, generating,
      agentIcon, statusClass, editAgent, closeDialog, saveAgent, toggleActive, testAgent,
      deleteAgent, deleteAllAgents, handleGenerate
    }
  }
}
</script>

<style scoped>
.agent-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.agent-icon { font-size: 24px; margin-right: 8px; }
.agent-name { font-size: 18px; font-weight: 700; margin-right: 8px; }
.agent-section { padding: 10px 0; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
.section-label { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 4px; }
.prompt-preview { font-size: 12px; color: var(--text-dim); padding: 8px; background: var(--bg); border-radius: 4px; line-height: 1.5; white-space: pre-wrap; }
.cap-tag { background: rgba(59,130,246,0.12); color: var(--blue); padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 500; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.status-dot.on { background: var(--green); box-shadow: 0 0 6px var(--green); }
.status-dot.off { background: var(--red); }
.creator { background: rgba(59,130,246,0.15); color: var(--blue); }
.supervisor { background: rgba(245,158,11,0.15); color: var(--accent); }
.reader { background: rgba(139,92,246,0.15); color: #a78bfa; }
.delete-btn {
  position: absolute; top: 8px; right: 8px;
  width: 24px; height: 24px; border-radius: 50%;
  border: none; background: transparent;
  color: var(--text-dim); cursor: pointer;
  font-size: 12px; line-height: 1;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.delete-btn:hover { background: var(--red); color: #fff; }
</style>
