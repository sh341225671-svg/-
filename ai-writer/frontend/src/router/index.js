import { createRouter, createWebHistory } from 'vue-router'
import ProjectList from '../views/ProjectList.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import ChapterEditor from '../views/ChapterEditor.vue'
import AdminAgents from '../views/AdminAgents.vue'
import WorkflowView from '../views/WorkflowView.vue'

const routes = [
  { path: '/', redirect: '/projects' },
  { path: '/projects', name: 'projects', component: ProjectList, meta: { title: '项目管理' } },
  { path: '/projects/:id', name: 'project', component: ProjectDetail, meta: { title: '项目详情' } },
  { path: '/chapter/:id', name: 'chapter', component: ChapterEditor, meta: { title: '章节写作' } },
  { path: '/admin/agents', name: 'admin-agents', component: AdminAgents, meta: { title: 'Agent 管理' } },
  { path: '/workflow', name: 'workflow', component: WorkflowView, meta: { title: '创作流水线' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
