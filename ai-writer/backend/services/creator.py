"""AI 创作者服务 - 负责小说章节的自动写作"""
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..models import Project, Chapter, Character, Volume, MemoryRecord
from ..services.ai import call_deepseek
import json
from typing import Optional

CREATOR_SYSTEM_PROMPT = """你是一位资深小说创作者，名叫言灵·创作者。
你的任务是根据项目设定和写作目标，创作高质量的小说章节。

【核心原则】
1. 严格遵循项目的主控思想——这是小说的灵魂，每一章都要体现
2. 保持所有角色性格、关系的一致性
3. 世界观规则不能自相矛盾
4. 注意伏笔的铺设与节奏——不急不缓

【写作风格要求】
- 使用小说的叙事语言，不要用说明性文字
- 对话使用中文引号「」
- 每章控制在 3000-5000 字
- 段落之间注意节奏变化
- 合理运用场景切换和时空跳跃"""


class CreatorService:

    def _build_context(self, project: Project, db: Session) -> str:
        """构建 L1-L4 全景上下文"""
        ctx_parts = []

        # L1 世界观
        if project.world_setting:
            try:
                ws = json.loads(project.world_setting) if isinstance(
                    project.world_setting, str) else project.world_setting
                ctx_parts.append(
                    f"【🌍 世界观设定】\n{json.dumps(ws, ensure_ascii=False, indent=2)}")
            except (json.JSONDecodeError, TypeError):
                ctx_parts.append(f"【🌍 世界观设定】\n{project.world_setting}")

        # 主控思想
        if project.core_theme:
            ctx_parts.append(
                f"【💡 主控思想 - 这是小说的灵魂】\n{project.core_theme}")

        # L2 角色库
        characters = db.query(Character).filter(
            Character.project_id == project.id).all()
        if characters:
            char_lines = []
            for c in characters:
                profile = c.profile_dict if c.profile else {}
                arc = c.arc_dict if c.arc else {}
                rels = c.relationships_dict if c.relationships else {}
                char_lines.append(f"- {c.name}（{c.role}）")
                if profile:
                    char_lines.append(
                        f"  人设：{json.dumps(profile, ensure_ascii=False)}")
                if arc:
                    char_lines.append(
                        f"  成长弧：{json.dumps(arc, ensure_ascii=False)}")
                if rels:
                    char_lines.append(
                        f"  关系：{json.dumps(rels, ensure_ascii=False)}")
            ctx_parts.append(f"【👤 角色库】\n" + "\n".join(char_lines))

        # L3 故事线 - 之前章节概要
        volumes = db.query(Volume).filter(
            Volume.project_id == project.id).order_by(Volume.vol_order).all()
        prev_chapters = []
        for v in volumes:
            chs = db.query(Chapter).filter(
                Chapter.volume_id == v.id,
                Chapter.content.isnot(None),
                Chapter.content != ""
            ).order_by(Chapter.chapter_order).all()
            prev_chapters.extend(chs)

        if prev_chapters:
            summaries = []
            for ch in prev_chapters[-5:]:
                summary = ch.content[:200] if ch.content else ""
                summaries.append(
                    f"  第{ch.chapter_order}章「{ch.title}」：{summary}...")
            ctx_parts.append(
                f"【📖 已写章节概要（最近{min(len(prev_chapters), 5)}章）】\n" + "\n".join(summaries))

        # L4 风格基线
        baseline = db.query(MemoryRecord).filter(
            MemoryRecord.project_id == project.id,
            MemoryRecord.key == "style_baseline"
        ).first()
        if baseline and baseline.content:
            ctx_parts.append(f"【🎨 风格基线】\n{baseline.content}")

        return "\n\n".join(ctx_parts)

    async def auto_write(self, project_id: int, chapter_id: int, db: Session, request: Optional[str] = None) -> Dict[str, Any]:
        """全自动写作"""
        project = db.query(Project).filter(
            Project.id == project_id).first()
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not project or not chapter:
            return {"status": "error", "message": "项目或章节不存在"}

        context = self._build_context(project, db)

        # 查询所属分卷信息
        volume = db.query(Volume).filter(
            Volume.id == chapter.volume_id).first()
        vol_info = f"第{volume.vol_order}卷「{volume.title}」" if volume else ""

        system_prompt = f"{CREATOR_SYSTEM_PROMPT}\n\n## 当前项目上下文\n{context}"

        writing_req = f"\n【用户写作需求】\n{request}\n" if request else ""
        user_prompt = (
            f"请为小说《{project.title}》创作{vol_info}的第{chapter.chapter_order}章。\n\n"
            f"【章节标题】{chapter.title}\n"
            f"【写作思路】{chapter.writing_notes or '请根据已有设定自然推进情节'}\n"
            f"{writing_req}"
            f"要求：\n"
            f"1. 直接输出小说正文，不要加任何说明或注释\n"
            f"2. 注意与前面章节的情节连贯\n"
            f"3. 如果有尚未兑现的伏笔，可以在本章适当推进\n"
            f"4. 保持角色性格一致"
        )

        content = await call_deepseek(
            system_prompt, user_prompt, temperature=0.7, max_tokens=8192)

        if content:
            chapter.content = content
            chapter.status = "writing"
            if chapter.version:
                chapter.version += 1
            else:
                chapter.version = 1
            db.commit()

            # 更新 L5 章节记忆
            summary_text = content[:500]
            existing_mem = db.query(MemoryRecord).filter(
                MemoryRecord.project_id == project_id,
                MemoryRecord.key == f"chapter_{chapter_id}_summary"
            ).first()
            mem_data = json.dumps(
                {"summary": summary_text, "chapter_order": chapter.chapter_order,
                    "title": chapter.title},
                ensure_ascii=False
            )
            if existing_mem:
                existing_mem.content = mem_data
            else:
                db.add(MemoryRecord(
                    project_id=project_id,
                    memory_level="L5",
                    key=f"chapter_{chapter_id}_summary",
                    content=mem_data
                ))
            db.commit()

        return {
            "status": "ok",
            "content": content or "",
            "assessment": {
                "quality": "ai_generated" if content else "failed",
                "issues": [] if content else ["AI 生成失败"],
                "tone": "auto",
                "style_match": 0.8,
            },
        }

    async def fill_skeleton(self, skeleton: str, context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """半自动：根据骨架填充正文"""
        chapter_id = context.get("chapter_id", 0)
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()

        system_prompt = CREATOR_SYSTEM_PROMPT
        user_prompt = (
            f"请根据以下小说章节骨架填充完整正文：\n\n"
            f"【骨架】\n{skeleton}\n\n"
            f"要求：\n"
            f"1. 以骨架为纲，展开描写\n"
            f"2. 填充对话、场景、心理描写\n"
            f"3. 保持叙事流畅\n"
            f"4. 直接输出填充后的正文，不要加说明"
        )

        content = await call_deepseek(
            system_prompt, user_prompt, temperature=0.7, max_tokens=8192)

        if content and chapter:
            chapter.content = content
            if chapter.version:
                chapter.version += 1
            else:
                chapter.version = 1
            db.commit()

        return {
            "status": "ok",
            "content": content or "",
            "assessment": {"quality": "good", "issues": []},
        }

    async def rewrite_section(self, content: str, instruction: str) -> Dict[str, Any]:
        """半自动：按指令重写段落"""
        system_prompt = (
            "你是一位小说润色专家。请根据用户的要求改写原文段落。\n"
            "保持原有的叙事风格和角色语气。\n"
            "只返回改写后的内容，不要加任何说明。"
        )
        user_prompt = (
            f"【需改写的段落】\n{content}\n\n"
            f"【修改要求】\n{instruction}"
        )

        rewritten = await call_deepseek(
            system_prompt, user_prompt, temperature=0.6, max_tokens=4096)

        return {
            "status": "ok",
            "rewritten": rewritten or content,
            "original_length": len(content),
            "rewritten_length": len(rewritten or ""),
        }
