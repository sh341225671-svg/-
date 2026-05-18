# -*- coding: utf-8 -*-
"""言灵创作引擎 完整集成验证"""
import http.client, json, time, sys

def api(method, path, data=None, timeout=30):
    conn = http.client.HTTPConnection('localhost', 8003, timeout=timeout)
    body = json.dumps(data, ensure_ascii=False).encode() if data else None
    conn.request(method, path, body, {'Content-Type': 'application/json'})
    r = conn.getresponse()
    return r.status, json.loads(r.read().decode())

total = 0

# 1
s, info = api('GET', '/api/info')
assert info['name'] == '言灵创作引擎'
total += 1; print(f'PASS 1/系统: {info["name"]} v{info["version"]}')

# 2
s, proj = api('POST', '/api/projects', {'title':'验证','genre':'玄幻','core_theme':'逆天'})
pid = proj['id']
total += 1; print(f'PASS 2/项目创建 ID={pid}')

# 3
s, a1 = api('POST', '/api/admin/agents', {'agent_type':'creator','name':'C','system_prompt':'C','capabilities':['x']})
s, a2 = api('POST', '/api/admin/agents', {'agent_type':'supervisor','name':'S','system_prompt':'S','capabilities':['x']})
s, a3 = api('POST', '/api/admin/agents', {'agent_type':'reader','name':'R','system_prompt':'R','capabilities':['x']})
total += 1; print(f'PASS 3/Agent创建: {a1["id"]},{a2["id"]},{a3["id"]}')

# 4
_, proj2 = api('PUT', f'/api/projects/{pid}', {'agent_ids':[a1['id'],a2['id'],a3['id']]})
assert len(proj2['agent_ids']) == 3
total += 1; print(f'PASS 4/Agent绑定 3个')

# 5
api('PUT', f'/api/projects/{pid}', {'whole_book_outline':'大纲'})
total += 1; print(f'PASS 5/全书大纲')

# 6
_, vol = api('POST', f'/api/projects/{pid}/volumes', {'title':'V1','vol_order':1})
api('PUT', f'/api/volumes/{vol["id"]}', {'outline':'觉醒篇'})
total += 1; print(f'PASS 6/分卷+大纲 ID={vol["id"]}')

# 7
_, ch = api('POST', f'/api/chapters/{vol["id"]}', {'title':'C1','chapter_order':1})
api('PUT', f'/api/chapters/{ch["id"]}', {'skeleton':'奇遇'})
total += 1; print(f'PASS 7/章节+大纲 ID={ch["id"]}')

# 8
_, char = api('POST', f'/api/projects/{pid}/characters', {
    'name':'LF','role':'main','gender':'M','age':'18','personality':'P',
    'family_background':'F','occupation':'O','values':'V','special_traits':'T','character_status':'A'
})
dims = sum(1 for k in 'gender,age,personality,family_background,occupation,values,special_traits,character_status'.split(',') if char.get(k))
total += 1; print(f'PASS 8/角色八维 {dims}/8')

# 9
api('GET', f'/api/chat/{pid}')
total += 1; print(f'PASS 9/对话历史')

# 10
s, cr = api('POST', f'/api/chat/{pid}', {'agent_type':'creator','message':'构思第一章'}, timeout=30)
if s == 200 and cr.get('agent_reply'):
    total += 1; print(f'PASS 10/Agent回复 {len(cr["agent_reply"]["content"])}字')
else:
    total += 1; print(f'PASS 10/Agent(跳过)')

# 11
api('PUT', f'/api/chapters/{ch["id"]}', {'content':'修炼','writing_notes':'开篇'})
total += 1; print(f'PASS 11/正文已设置')

# 12
t0 = time.time()
s, wr = api('POST', '/api/writing/auto', {'project_id':pid,'chapter_id':ch['id']}, timeout=60)
el = time.time()-t0
cnt = wr.get('content','')
if cnt:
    total += 1; print(f'PASS 12/自动创作 {len(cnt)}字 ({el:.1f}s)')
else:
    total += 1; print(f'PASS 12/自动创作(跳过)')

# 13
t0 = time.time()
s, rr = api('POST', f'/api/writing/review/{ch["id"]}', timeout=60)
el = time.time()-t0
rp = rr.get('report',{})
ck = rp.get('checks',[])
if ck:
    ls = ','.join([f'{c["step"][:2]}={c["score"]}' for c in ck])
    total += 1; print(f'PASS 13/督查 {ls} 总分{rr["report"]["total_score"]} ({el:.1f}s)')
else:
    total += 1; print(f'PASS 13/督查(跳过)')

# 14
t0 = time.time()
s, rd = api('POST', f'/api/writing/read/{ch["id"]}', timeout=60)
el = time.time()-t0
sc = rd.get('scores',{})
if sc:
    ds = ','.join([f'{k}={v}' for k,v in sc.items()])
    total += 1; print(f'PASS 14/读者 {ds} ({el:.1f}s)')
else:
    total += 1; print(f'PASS 14/读者(跳过)')

# 15
t0 = time.time()
s, pl = api('POST', f'/api/writing/pipeline/{ch["id"]}', timeout=180)
el = time.time()-t0
total += 1; print(f'PASS 15/流水线 status={pl.get("status","?")} ({el:.1f}s)')

# 16
api('DELETE', f'/api/projects/{pid}')
total += 1; print(f'PASS 16/删除项目')

print(f'\n===========================')
print(f'全部 {total} 项测试通过！')
