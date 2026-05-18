"""项目 - Agent 对话路由（分区管理版）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import json, re

from ..database import get_db
from ..models import Project, Chapter, Character, Volume, AgentConfig, ChatMessage
from ..services.ai import call_deepseek

router = APIRouter(prefix="/api/chat")

SECTION_LABELS = {
    "world": "世界观设定",
    "outline": "全书大纲",
    "characters": "角色设定",
    "chapters": "章节大纲",
    "general": "综合创作",
}

SECTION_INSTRUCTIONS = {
    "world": "请围绕世界观设定展开讨论：世界规则、地理环境、历史背景、势力分布、文化风俗、力量/科技体系等。请具体描述而非抽象概括。",
    "outline": "请围绕全书大纲展开讨论：核心冲突、主线走向、分卷规划、情节节点、伏笔安排、节奏控制等。请结构化呈现。",
    "characters": "请围绕角色设定展开讨论：外观性格、动机目标、成长弧光、人物关系、八维塑造（性别/年龄/性格/家庭背景/职业/价值观/特殊习惯/状态）。创建角色时请用结构化描述。",
    "chapters": "请围绕章节内容展开讨论：章节情节安排、起承转合、核心冲突、衔接节奏、场景设计等。",
    "general": "综合创作讨论，自由发挥。",
}


@router.get("/{project_id}")
async def get_chat_history(
    project_id: int,
    agent_type: Optional[str] = None,
    section: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """获取项目某分区的对话历史"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    q = db.query(ChatMessage).filter(ChatMessage.project_id == project_id)
    if agent_type:
        q = q.filter(ChatMessage.agent_type == agent_type)
    if section:
        q = q.filter(ChatMessage.section == section)
    messages = q.order_by(ChatMessage.created_at.asc()).limit(limit).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "agent_type": m.agent_type,
            "section": m.section or "general",
            "agent_config_id": m.agent_config_id,
            "content": m.content,
            "metadata": json.loads(m.meta_data) if m.meta_data else None,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.post("/{project_id}")
async def send_message(project_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """向项目 Agent 发送消息并获取回复（分区上下文感知）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    agent_type = body.get("agent_type", "creator")
    message = body.get("message", "")
    section = body.get("section", "general")
    if not message:
        raise HTTPException(400, "message is required")
    if section not in SECTION_LABELS:
        section = "general"

    # 查找绑定的 Agent
    agent = None
    for a in (project.agent_configs or []):
        if a.agent_type == agent_type and a.is_active:
            agent = a
            break

    # 保存用户消息（带 section 标记）
    user_msg = ChatMessage(
        project_id=project_id,
        role="user",
        agent_type=agent_type,
        section=section,
        agent_config_id=agent.id if agent else None,
        content=message,
    )
    db.add(user_msg)
    db.commit()

    # 构建系统提示词
    system_prompt = agent.system_prompt if (agent and agent.system_prompt) else "你是一位AI创作助手。"

    # 加载项目上下文 + 本分区最近历史
    context_parts = [
        f"项目名称：{project.title}",
        f"类型：{project.genre}",
        f"主控思想：{project.core_theme or '未设置'}",
    ]

    # 分卷与章节
    volumes = db.query(Volume).filter(Volume.project_id == project_id).order_by(Volume.vol_order).all()
    if volumes:
        vol_lines = []
        for v in volumes:
            chs = db.query(Chapter).filter(Chapter.volume_id == v.id).order_by(Chapter.chapter_order).all()
            vol_lines.append(f"- {v.title}（{len(chs)}章）大纲：{(v.outline or '')[:100]}")
            for c in chs[-2:]:
                if c.skeleton:
                    vol_lines.append(f"  · {c.title}：{c.skeleton[:60]}")
        context_parts.append("分卷情况：\n" + "\n".join(vol_lines))

    if project.whole_book_outline:
        context_parts.append(f"全书大纲：{project.whole_book_outline[:500]}")

    # 世界观
    if project.world_setting:
        try:
            ws = json.loads(project.world_setting) if isinstance(project.world_setting, str) else project.world_setting
            ws_str = json.dumps(ws, ensure_ascii=False, indent=2)[:500] if isinstance(ws, dict) else str(ws)[:500]
        except Exception:
            ws_str = str(project.world_setting)[:500]
        context_parts.append(f"世界观：{ws_str}")

    # 角色
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    if characters:
        char_lines = []
        for c in characters:
            dims = [f"{k}={v}" for k, v in c.char_dict.items() if v]
            char_lines.append(f"- {c.name}（{c.role}）{' '.join(dims)}")
        context_parts.append("角色：\n" + "\n".join(char_lines))

    # 本分区的最近对话历史
    recent = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id,
        ChatMessage.section == section,  # 只查本分区
    ).order_by(ChatMessage.created_at.desc()).limit(8).all()
    if recent:
        history = []
        for m in reversed(recent):
            role_label = "用户" if m.role == "user" else m.agent_type or "助手"
            history.append(f"{role_label}：{m.content[:200]}")
        context_parts.append(f"本{section}对话历史：\n" + "\n".join(history))

    context = "\n\n".join(context_parts)
    section_instruction = SECTION_INSTRUCTIONS.get(section, SECTION_INSTRUCTIONS["general"])

    full_prompt = (
        f"{system_prompt}\n\n"
        f"## 项目情况\n{context}\n\n"
        f"## 当前区域\n{SECTION_LABELS.get(section, '综合创作')}\n\n"
        f"{section_instruction}\n\n"
        f"## 用户消息\n{message}\n\n"
        f"### 标记约定\n"
        f"自动收录标记（没有就不加）：\n"
        f"📌 世界观要点 / 📌 大纲要点 / 📌 角色要点 / 📌 分卷要点 / 📌 章节要点\n"
        f"正常回复即可，不需要刻意使用标记。"
    )

    result = await call_deepseek(full_prompt, message, temperature=0.6, max_tokens=4096)
    reply = result or "（AI 暂时无法回复，请稍后重试）"

    # 自动同步
    auto_actions = _extract_and_apply(reply, project_id, db, section)

    meta = {"model": "deepseek-chat", "section": section}
    if auto_actions:
        meta["auto_actions"] = auto_actions

    agent_msg = ChatMessage(
        project_id=project_id,
        role="agent",
        agent_type=agent_type,
        section=section,
        agent_config_id=agent.id if agent else None,
        content=reply,
        meta_data=json.dumps(meta, ensure_ascii=False),
    )
    db.add(agent_msg)
    db.commit()

    return {
        "user_message": {"id": user_msg.id, "content": message},
        "agent_reply": {
            "id": agent_msg.id,
            "content": reply,
            "agent_type": agent_type,
            "agent_name": agent.name if agent else f"{agent_type}",
            "section": section,
            "auto_actions": auto_actions,
        },
    }


@router.post("/{project_id}/sync/{message_id}")
async def sync_message(project_id: int, message_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """手动将某条 Agent 回复同步到项目中"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.project_id == project_id,
        ChatMessage.role == "agent",
    ).first()
    if not msg:
        raise HTTPException(404, "Agent message not found")

    section = body.get("section") or msg.section or "general"
    content = msg.content

    if section == "world":
        try:
            parsed = json.loads(content)
            project.world_setting_dict = parsed
        except Exception:
            project.world_setting = json.dumps({"agent_generated": content}, ensure_ascii=False)
        db.commit()
        return {"detail": "世界观已同步更新", "section": "world"}

    elif section == "outline":
        project.whole_book_outline = (project.whole_book_outline or "") + "\n\n" + content
        db.commit()
        return {"detail": "全书大纲已同步更新", "section": "outline"}

    elif section == "characters":
        # 尝试提取角色信息
        names = re.findall(r"[（(]?[姓名名称]{2}[：:]\s*(\S+)|(?<=角色[：:])\s*(\S+)", content)
        target = body.get("target", "")
        name = target or (names[0][0] or names[0][1] if names else "新角色")
        existing = db.query(Character).filter(
            Character.project_id == project_id, Character.name == name
        ).first()
        if not existing:
            char = Character(project_id=project_id, name=name, role="配角", personality=content[:500])
            db.add(char)
            db.commit()
            return {"detail": f"角色「{name}」已创建", "section": "characters"}
        return {"detail": f"角色「{name}」已存在", "section": "characters"}

    elif section == "chapters":
        # 查找第一个分卷
        vol = db.query(Volume).filter(Volume.project_id == project_id).order_by(Volume.vol_order).first()
        if vol:
            ch_count = db.query(Chapter).filter(Chapter.volume_id == vol.id).count()
            ch = Chapter(
                volume_id=vol.id,
                title=body.get("target", f"第{ch_count+1}章"),
                chapter_order=ch_count + 1,
                skeleton=content[:2000],
            )
            db.add(ch)
            db.commit()
            return {"detail": "章节已创建，大纲已保存", "section": "chapters"}
        return {"detail": "请先创建分卷", "section": "chapters"}

    return {"detail": "已同步", "section": section}


@router.post("/{project_id}/reparse/{message_id}")
async def reparse_and_sync(project_id: int, message_id: int, db: Session = Depends(get_db)):
    """对某条已保存的 Agent 回复重新执行结构化解析"""
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.project_id == project_id,
    ).first()
    if not msg:
        raise HTTPException(404, "Message not found")
    actions = _extract_and_apply(msg.content, project_id, db, msg.section or "general")
    return {"detail": "解析完成", "actions": actions}


@router.delete("/{project_id}")
async def clear_chat_history(
    project_id: int,
    agent_type: Optional[str] = None,
    section: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """清除项目的对话历史（可按分区/Agent过滤）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    q = db.query(ChatMessage).filter(ChatMessage.project_id == project_id)
    if agent_type:
        q = q.filter(ChatMessage.agent_type == agent_type)
    if section:
        q = q.filter(ChatMessage.section == section)

    deleted = q.delete(synchronize_session=False)
    db.commit()
    return {"detail": f"cleared {deleted} messages", "count": deleted}


# ----- 结构化解析函数（与之前一致，无需改动）-----

def _extract_and_apply(reply: str, project_id: int, db: Session, section: str = "general") -> list:
    """解析回复中的标记内容并自动应用到项目"""
    actions = []

    for m in re.finditer(r"[📌⭐📍]\s*世界观[要点：:]\s*(.+?)(?=[📌⭐📍]|\Z)", reply, re.DOTALL):
        content = m.group(1).strip()
        if len(content) > 20:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                existing = {}
                try:
                    existing = json.loads(project.world_setting) if project.world_setting else {}
                except Exception:
                    existing = {}
                if isinstance(existing, str):
                    existing = {"content": existing}
                existing["agent_generated"] = existing.get("agent_generated", "") + "\n\n" + content
                project.world_setting_dict = existing
                db.commit()
                actions.append({"action": "update_world", "label": "世界观已更新"})

    for m in re.finditer(r"[📌⭐📍]\s*大纲[要点：:]\s*(.+?)(?=[📌⭐📍]|\Z)", reply, re.DOTALL):
        content = m.group(1).strip()
        if len(content) > 20:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                existing = project.whole_book_outline or ""
                project.whole_book_outline = existing + ("\n\n" if existing else "") + content
                db.commit()
                actions.append({"action": "update_outline", "label": "全书大纲已更新"})

    for m in re.finditer(r"[📌⭐📍]\s*角色[要点：:]\s*(.+?)(?=[📌⭐📍]|\Z)", reply, re.DOTALL):
        block = m.group(1).strip()
        name_match = re.search(r"(?:姓名|名称|名字)[：:]\s*(\S+)", block)
        name = name_match.group(1) if name_match else "新角色"
        existing = db.query(Character).filter(
            Character.project_id == project_id, Character.name == name
        ).first()
        if not existing:
            char = Character(project_id=project_id, name=name, role="配角")
            for field, label in [
                ("gender", r"(?:性别)[：:]\s*(\S+)"),
                ("age", r"(?:年龄)[：:]\s*(\S+)"),
                ("personality", r"(?:性格|人格)[：:]\s*(.+?)(?=\n|$)"),
                ("family_background", r"(?:家庭背景|出身)[：:]\s*(.+?)(?=\n|$)"),
                ("occupation", r"(?:职业)[：:]\s*(\S+)"),
                ("values", r"(?:价值观)[：:]\s*(.+?)(?=\n|$)"),
                ("special_traits", r"(?:特殊|习惯|特点)[：:]\s*(.+?)(?=\n|$)"),
            ]:
                fm = re.search(label, block)
                if fm:
                    setattr(char, field, fm.group(1))
            db.add(char)
            db.commit()
            actions.append({"action": "add_character", "label": f"角色「{name}」已创建"})

    for m in re.finditer(r"[📌⭐📍]\s*分卷[要点：:]\s*(.+?)(?=[📌⭐📍]|\Z)", reply, re.DOTALL):
        block = m.group(1).strip()
        title_match = re.search(r"(?:卷名|名称|标题)[：:]\s*(\S+)", block)
        title = title_match.group(1) if title_match else "新分卷"
        outline = block[:1000]
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            vol = Volume(
                project_id=project_id, title=title,
                vol_order=db.query(Volume).filter(Volume.project_id == project_id).count() + 1,
                outline=outline,
            )
            db.add(vol)
            db.commit()
            actions.append({"action": "add_volume", "label": f"分卷「{title}」已创建"})

    for m in re.finditer(r"[📌⭐📍]\s*章节[要点：:]\s*(.+?)(?=[📌⭐📍]|\Z)", reply, re.DOTALL):
        block = m.group(1).strip()
        title_match = re.search(r"(?:章名|标题|名称)[：:]\s*(\S+)", block)
        ch_title = title_match.group(1) if title_match else "新章节"
        skeleton = block[:2000]
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            vol = db.query(Volume).filter(
                Volume.project_id == project_id
            ).order_by(Volume.vol_order.desc()).first()
            if vol:
                ch = Chapter(
                    volume_id=vol.id, title=ch_title,
                    chapter_order=db.query(Chapter).filter(Chapter.volume_id == vol.id).count() + 1,
                    skeleton=skeleton,
                )
                db.add(ch)
                db.commit()
                actions.append({"action": "add_chapter", "label": f"章节「{ch_title}」已创建"})

    return actions


@router.post("/{project_id}/apply")
async def apply_from_chat(project_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """向后兼容：手动应用对话内容"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    action = body.get("action", "")
    content = body.get("content", "")
    target = body.get("target", "")

    if action == "set_world_setting":
        try:
            project.world_setting_dict = json.loads(content) if isinstance(content, str) and content.startswith("{") else content
        except Exception:
            project.world_setting = content
        db.commit()
        return {"detail": "世界观已更新"}
    elif action == "set_book_outline":
        project.whole_book_outline = content
        db.commit()
        return {"detail": "全书大纲已更新"}
    elif action == "add_character":
        name = target or "新角色"
        char = Character(project_id=project_id, name=name, role="配角", personality=content[:500])
        db.add(char)
        db.commit()
        return {"detail": f"角色「{name}」已添加"}
    elif action == "add_volume":
        vol = Volume(project_id=project_id, title=target or "新分卷",
                     vol_order=len(db.query(Volume).filter(Volume.project_id == project_id).all()) + 1,
                     outline=content[:1000])
        db.add(vol)
        db.commit()
        return {"detail": f"分卷「{vol.title}」已添加"}
    elif action == "add_chapter":
        volume_id = body.get("volume_id")
        if not volume_id:
            raise HTTPException(400, "volume_id required")
        vol = db.query(Volume).filter(Volume.id == volume_id).first()
        if not vol:
            raise HTTPException(404, "Volume not found")
        ch_count = db.query(Chapter).filter(Chapter.volume_id == volume_id).count()
        ch = Chapter(volume_id=volume_id, title=target or f"第{ch_count+1}章",
                     chapter_order=ch_count + 1, skeleton=content[:2000])
        db.add(ch)
        db.commit()
        return {"detail": f"章节「{ch.title}」已添加，大纲已保存"}
    raise HTTPException(400, f"Unknown action: {action}")
