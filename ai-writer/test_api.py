"""灵枢 API 快速验证"""
import urllib.request, json, sys

API = 'http://localhost:8002'

def api(method, path, data=None):
    url = API + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body,
        headers={'Content-Type':'application/json'}, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

def ok(label, result):
    s = json.dumps(result, ensure_ascii=False, indent=2)[:120]
    print(('[OK] ' + label + ': ' + s).encode('utf-8', errors='replace').decode('utf-8'))

# 0. Root
ok('API info', api('GET', '/api/info'))

# 1. 创建项目
print('\n📚 项目')
pid = 1
proj = api('POST', '/api/projects', {
    'title': '天穹觉醒', 'genre': '玄幻',
    'core_theme': '生命的韧性高于一切苦难',
    'target_audience': '网文读者'
})
ok('创建项目', proj)

projs = api('GET', '/api/projects')
ok(f'项目列表 ({len(projs)}个)', projs)

proj_detail = api('GET', f'/api/projects/{pid}')
ok('项目详情', proj_detail)

# 2. 分卷
print('\n📦 分卷')
vol = api('POST', f'/api/projects/{pid}/volumes', {
    'title': '第一卷 觉醒', 'vol_order': 1, 'summary': '主角的觉醒之路'
})
ok('创建分卷', vol)

vols = api('GET', f'/api/projects/{pid}/volumes')
ok(f'分卷列表 ({len(vols)}个)', vols)
vid = vol['id']

# 3. 章节
print('\n📝 章节')
ch = api('POST', f'/api/chapters/{vid}', {
    'title': '第一章 未知的召唤', 'chapter_order': 1
})
ok('创建章节', ch)

upd = api('PUT', f'/api/chapters/{ch["id"]}', {
    'content': '夜幕降临，城市的灯火在远处闪烁。林轩站在窗前，目光穿过玻璃望向无尽的黑暗…他现在还不知道，这个普通的夜晚将改变一切。'
})
ok('更新章节', upd)

ch_detail = api('GET', f'/api/chapters/{ch["id"]}')
ok('章节详情', ch_detail)

# 4. 角色
print('\n👤 角色')
char = api('POST', f'/api/projects/{pid}/characters', {
    'name': '林轩', 'role': '主角'
})
ok('创建角色', char)

chars = api('GET', f'/api/projects/{pid}/characters')
ok(f'角色列表 ({len(chars)}个)', chars)

# 5. Agent 管理（后台操作口子）
print('\n⚙️ Agent 管理')
# 创建三个 Agent
for info in [
    ('creator', '灵枢·创作者',
     '你是一位擅长东方玄幻的作家，文风热烈细腻，注重人物成长弧光。创作时严格遵循世界观设定和角色性格一致性。',
     ['世界观构建', '角色弧光设计', '节奏控制', '伏笔埋设', '对话打磨']),
    ('supervisor', '明镜·督查者',
     '你是一位严格的小说编辑。按固定顺序检查：戏剧必需性→价值转换→冲突真实性→一致性→风格。评分1-10，低于7分给出修改建议。',
     ['戏剧性分析', '价值转换评估', '冲突真实性验证', '一致性检查', '风格分析']),
    ('reader', '灵枢·读者',
     '你是一位资深网文读者，喜爱玄幻题材。按六个维度评分并给出真实感受的读后反馈。',
     ['沉浸感评估', '情感共鸣', '逻辑合理性', '人物魅力', '节奏感', '期待感']),
]:
    agent = api('POST', '/api/admin/agents', {
        'agent_type': info[0], 'name': info[1],
        'system_prompt': info[2], 'capabilities': info[3]
    })
    ok(f'创建 {info[0]}: {info[1]}', agent)

agents = api('GET', '/api/admin/agents')
ok(f'Agent 列表 ({len(agents)}个)', agents)

# 更新 Agent 配置
if agents:
    aid = agents[0]['id']
    upd_agent = api('PUT', f'/api/admin/agents/{aid}', {
        'system_prompt': '【更新版】' + agents[0]['system_prompt']
    })
    ok('更新 Agent', upd_agent)

# 6. 写作接口 (桩)
print('\n✍️ 写作测试')
write_result = api('POST', '/api/writing/auto', {
    'project_id': pid, 'chapter_id': ch['id'],
    'request': '写一段林轩觉醒的场景，展现他的内心挣扎'
})
ok('全自动写作', write_result)

review_result = api('POST', f'/api/writing/review/{ch["id"]}')
ok('督查者审校', review_result)

read_result = api('POST', f'/api/writing/read/{ch["id"]}')
ok('读者反馈', read_result)

print('\n🎉 全部 API 测试通过！')
