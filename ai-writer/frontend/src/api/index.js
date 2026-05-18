import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

export function useApi() {
  return {
    // ===== 项目 =====
    getProjects: () => api.get('/api/projects'),
    createProject: (data) => api.post('/api/projects', data),
    getProject: (id) => api.get(`/api/projects/${id}`),
    updateProject: (id, data) => api.put(`/api/projects/${id}`, data),
    deleteProject: (id) => api.delete(`/api/projects/${id}`),

    // ===== 分卷 =====
    getVolumes: (pid) => api.get(`/api/projects/${pid}/volumes`),
    createVolume: (pid, data) => api.post(`/api/projects/${pid}/volumes`, data),
    updateVolume: (vid, data) => api.put(`/api/volumes/${vid}`, data),
    deleteVolume: (vid) => api.delete(`/api/volumes/${vid}`),

    // ===== 章节 =====
    getChapter: (id) => api.get(`/api/chapters/${id}`),
    updateChapter: (id, data) => api.put(`/api/chapters/${id}`, data),
    createChapter: (vid, data) => api.post(`/api/chapters/${vid}`, data),
    deleteChapter: (cid) => api.delete(`/api/chapters/${cid}`),

    // ===== 角色 =====
    getCharacters: (pid) => api.get(`/api/projects/${pid}/characters`),
    createCharacter: (pid, data) => api.post(`/api/projects/${pid}/characters`, data),
    updateCharacter: (pid, cid, data) => api.put(`/api/projects/${pid}/characters/${cid}`, data),
    deleteCharacter: (pid, cid) => api.delete(`/api/projects/${pid}/characters/${cid}`),

    // ===== Agent 管理（后台）=====
    getAgentConfigs: () => api.get('/api/admin/agents'),
    createAgentConfig: (data) => api.post('/api/admin/agents', data),
    getAgentConfig: (id) => api.get(`/api/admin/agents/${id}`),
    updateAgentConfig: (id, data) => api.put(`/api/admin/agents/${id}`, data),
    deleteAgentConfig: (id) => api.delete(`/api/admin/agents/${id}`),
    deleteAllAgentConfigs: () => api.delete('/api/admin/agents'),
    testAgent: (id, data) => api.post(`/api/admin/agents/${id}/test`, data),
    getAgentLogs: (params) => api.get('/api/admin/agents/logs', { params }),
    generateAgentConfig: (data) => api.post('/api/admin/agents/generate-config', data),

    // ===== 批量操作 =====
    deleteAllProjects: () => api.delete('/api/projects'),

    // ===== 写作 =====
    autoWrite: (data) => api.post('/api/writing/auto', data),
    fillSkeleton: (data) => api.post('/api/writing/semi/skeleton', data),
    rewriteSection: (data) => api.post('/api/writing/semi/rewrite', data),
    triggerReview: (cid) => api.post(`/api/writing/review/${cid}`),
    triggerRead: (cid) => api.post(`/api/writing/read/${cid}`),

    // ===== 伏笔 =====
    getForeshadows: (pid) => api.get(`/api/projects/${pid}/foreshadows`),
    createForeshadow: (pid, data) => api.post(`/api/projects/${pid}/foreshadows`, data),

    // ===== 对话系统 =====
    getChatMessages: (pid, agentType, section) => api.get(`/api/chat/${pid}`, { params: { agent_type: agentType, section: section } }),
    sendChatMessage: (pid, data) => api.post(`/api/chat/${pid}`, data),
    applyChatAction: (pid, data) => api.post(`/api/chat/${pid}/apply`, data),
    syncChatMessage: (pid, msgId, data) => api.post(`/api/chat/${pid}/sync/${msgId}`, data),
    reparseChatMessage: (pid, msgId) => api.post(`/api/chat/${pid}/reparse/${msgId}`),
    clearChatHistory: (pid, agentType, section) => api.delete(`/api/chat/${pid}`, { params: { agent_type: agentType, section: section } }),
    runPipeline: (cid) => api.post(`/api/writing/pipeline/${cid}`),
  }
}

export default api
