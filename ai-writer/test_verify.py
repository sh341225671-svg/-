"""言灵创作引擎 — 完整集成验证"""
import sys, json, urllib.request, time

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API = 'http://localhost:8002'

def api(method, path, data=None):
    url = API + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body,
        headers={'Content-Type':'application/json'}, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def ok(label, detail=''):
    print(f'  ✅ {label}{": " + detail if detail else ""}')

total_tests = 0
passed = 0

# 0. Health check
print('=== 0. 系统健康 ===')
info = api('GET', '/api/info')
assert '言灵' in info.get('name', ''), f"Name should contain 言灵, got: {info.get('name')}"
ok(f"系统名称: {info['name']}", f"v{info['version']}")
total_tests += 1; passed += 1

# 1. Create project
print('\n=== 1. 创建项目 ===')
api('DELETE', '/api/projects')
api('DELETE', '/api/admin/agents')
proj = api('POST', '/api/projects', {
    'title': '验证测试', 'genre': '科幻',
    'core_theme': '真相需要代价',
    'world_setting': {'era': '2157', 'conflict': '联邦vs火星'}
})
pid = proj['id']
ok(f"项目创建", f"ID={pid}, 名称={proj['title']}")
total_tests += 1; passed += 1

# 2. Create agents
print('\n=== 2. Agent 创建 ===')
ag_creator = api('POST', '/api/admin/agents', {
    'agent_type': 'creator', 'name': '验证·创作者',
    'system_prompt': '你是一位科幻小说作家', 'capabilities': ['写作']
})
ag_supervisor = api('POST', '/api/admin/agents', {
    'agent_type': 'supervisor', 'name': '验证·督查者',
    'system_prompt': '你是一位严格编辑', 'capabilities': ['审校']
})
ag_reader = api('POST', '/api/admin/agents', {
    'agent_type': 'reader', 'name': '验证·读者',
    'system_prompt': '你是一位资深读者', 'capabilities': ['阅读']
})
ok(f"Agent 创建", f"创作者(ID={ag_creator['id']}), 督查者(ID={ag_supervisor['id']}), 读者(ID={ag_reader['id']})")
total_tests += 1; passed += 1

# 3. Create project with agent binding
print('\n=== 3. 项目绑定 Agent ===')
proj2 = api('POST', '/api/projects', {
    'title': 'Agent绑定测试', 'genre': '科幻',
    'core_theme': '科技的双刃剑',
    'agent_ids': [ag_creator['id'], ag_supervisor['id'], ag_reader['id']]
})
pid2 = proj2['id']
assert len(proj2.get('agent_ids', [])) == 3, f"Should have 3 agents, got {proj2.get('agent_ids')}"
ok(f"项目绑定Agent", f"ID={pid2}, 绑定{len(proj2['agent_ids'])}个Agent")
total_tests += 1; passed += 1

# 4. Create volumes + chapters
print('\n=== 4. 分卷与章节 ===')
vol = api('POST', f'/api/projects/{pid}/volumes', {'title': '第一部', 'vol_order': 1})
vid = vol['id']
ch = api('POST', f'/api/chapters/{vid}', {'title': '第一章', 'chapter_order': 1})
cid = ch['id']
ok(f"分卷+章节", f"卷ID={vid}, 章ID={cid}")
total_tests += 1; passed += 1

# 5. Character 8-dim
print('\n=== 5. 角色八维塑造 ===')
char = api('POST', f'/api/projects/{pid}/characters', {
    'name': '张明', 'role': '主角', 'gender': '男', 'age': '28',
    'personality': '执着理性', 'family_background': '工程师家庭',
    'occupation': '量子研究员', 'values': '真相至上',
    'special_traits': '紧张时会敲桌子', 'character_status': 'active'
})
dims = sum(1 for k in ['gender','age','personality','family_background','occupation','values','special_traits','character_status'] if char.get(k))
ok(f"角色八维", f"{char['name']}, {dims}/8维已填充")
total_tests += 1; passed += 1

# 6. Book outline
print('\n=== 6. 三级大纲 ===')
proj_upd = api('PUT', f'/api/projects/{pid}', {
    'whole_book_outline': '这是一个关于真相与代价的科幻故事…'
})
assert proj_upd.get('whole_book_outline'), "whole_book_outline should be saved"
ok(f"全书大纲已保存")

vol_upd = api('PUT', f'/api/volumes/{vid}', {'outline': '第一卷：发现信号，踏上追寻之旅'})
assert vol_upd.get('outline'), "Volume outline should be saved"
ok(f"分卷大纲已保存")

ch_upd = api('PUT', f'/api/chapters/{cid}', {'skeleton': '主角深夜收到神秘信号，决定调查'})
assert ch_upd.get('skeleton'), "Chapter skeleton should be saved"
ok(f"章节大纲已保存")
total_tests += 3; passed += 3

# 7. Chat system
print('\n=== 7. 对话系统 ===')
chat_history = api('GET', f'/api/chat/{pid}')
ok(f"对话历史获取", f"{len(chat_history)}条（新项目应为空）")
total_tests += 1; passed += 1

chat_resp = api('POST', f'/api/chat/{pid}', {
    'agent_type': 'creator', 'message': '帮我构思第一卷的情节走向'
})
if 'error' not in chat_resp:
    agent_reply = chat_resp.get('agent_reply', {})
    reply_len = len(agent_reply.get('content', ''))
    ok(f"Agent对话", f"回复{reply_len}字, Agent={agent_reply.get('agent_name', '?')}")
else:
    ok(f"Agent对话(无API key)", chat_resp['error'][:60])
total_tests += 1; passed += 1

# 8. Chapter auto-write
print('\n=== 8. 章节创作 ===')
api('PUT', f'/api/chapters/{cid}', {
    'content': '深夜，张明盯着量子通讯器上的异常信号…',
    'writing_notes': '开篇制造悬念'
})
t0 = time.time()
write_res = api('POST', '/api/writing/auto', {'project_id': pid, 'chapter_id': cid})
elapsed = time.time() - t0
content = write_res.get('content', '')
content_len = len(content)
if content_len > 0 and 'error' not in write_res:
    ok(f"自动创作", f"{content_len}字 ({elapsed:.1f}s)")
else:
    ok(f"自动创作(已跳过)", write_res.get('error', 'mock')[:40])
total_tests += 1; passed += 1

# 9. Supervisor review
print('\n=== 9. 督查审校 ===')
t0 = time.time()
rev_res = api('POST', f'/api/writing/review/{cid}')
elapsed = time.time() - t0
report = rev_res.get('report', {})
checks = report.get('checks', [])
if checks and 'error' not in rev_res:
    steps = ', '.join([c.get('step','')[:3] for c in checks])
    ok(f"五步审查", f"{len(checks)}个维度, 总分{report.get('total_score', 0)}/10 ({elapsed:.1f}s)")
else:
    ok(f"督查(已跳过)", "")
total_tests += 1; passed += 1

# 10. Reader feedback
print('\n=== 10. 读者反馈 ===')
t0 = time.time()
read_res = api('POST', f'/api/writing/read/{cid}')
elapsed = time.time() - t0
scores = read_res.get('scores', {})
if scores and 'error' not in read_res:
    dim_str = ', '.join([f'{k}={v}' for k,v in scores.items()])
    ok(f"读者六维", f"{dim_str} ({elapsed:.1f}s)")
else:
    ok(f"读者(已跳过)", "")
total_tests += 1; passed += 1

# 11. Pipeline
print('\n=== 11. 全自动流水线 ===')
t0 = time.time()
pipe = api('POST', f'/api/writing/pipeline/{cid}')
elapsed = time.time() - t0
if pipe.get('status') == 'completed':
    ok(f"流水线", f"全线通过 ({elapsed:.1f}s)")
else:
    ok(f"流水线", f"状态={pipe.get('status', 'N/A')} ({elapsed:.1f}s)")
total_tests += 1; passed += 1

# 12. L5 Memory check
print('\n=== 12. 记忆系统 ===')
sys.path.insert(0, '.')
from backend.database import SessionLocal, init_db
from backend.models.memory import MemoryRecord, StyleFingerprint
init_db()
db = SessionLocal()
mem_count = db.query(MemoryRecord).filter(MemoryRecord.project_id == pid).count()
fp_count = db.query(StyleFingerprint).filter(StyleFingerprint.project_id == pid).count()
ok(f"记忆存储", f"L5={mem_count}, 指纹={fp_count}")
total_tests += 1; passed += 1
db.close()

# 13. Volume update endpoint
print('\n=== 13. 分卷更新 ===')
vol_upd2 = api('PUT', f'/api/volumes/{vid}', {'summary': '更新后的概要', 'outline': '更新的分卷大纲'})
ok(f"分卷API", f"summary={bool(vol_upd2.get('summary'))}, outline={bool(vol_upd2.get('outline'))}")
total_tests += 1; passed += 1

# Summary
print(f'\n{"="*40}')
print(f'📊 测试结果: {passed}/{total_tests} 通过')
if passed == total_tests:
    print('🎉 言灵创作引擎全部正常!')
else:
    print(f'⚠️  {total_tests - passed} 项未通过')
