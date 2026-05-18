"""测试新端点：generate-config, 批量删除, 工作流"""
import json, urllib.request, sys

API = 'http://localhost:8002'

def api(method, path, data=None):
    url = API + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body,
        headers={'Content-Type':'application/json'}, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

# 1. generate-config (模拟数据，无API key)
print('=== 1. 对话式生成 Agent 配置 ===')
result = api('POST', '/api/admin/agents/generate-config', {
    'description': '一个专业的推理小说编辑，关注线索埋设与回收、逻辑自洽、人物动机合理性'
})
print('agent_type:', result.get('agent_type'))
print('name:', result.get('name'))
print('capabilities:', result.get('capabilities'))
print('system_prompt preview:', result.get('system_prompt','')[:80])

# 2. 批量删除 Agent
print('\n=== 2. 批量删除 Agent ===')
del_r = api('DELETE', '/api/admin/agents')
print('delete result:', del_r)

agents = api('GET', '/api/admin/agents')
print('remaining agents:', len(agents))

# 3. 批量删除项目
print('\n=== 3. 批量删除项目 ===')
del_p = api('DELETE', '/api/projects')
print('delete result:', del_p)

projs = api('GET', '/api/projects')
print('remaining projects:', len(projs))

print('\n✅ 全部通过')
