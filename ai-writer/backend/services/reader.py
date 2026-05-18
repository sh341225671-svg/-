"""AI 深度网文读者服务"""
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..models import Chapter, Volume
from ..services.ai import call_deepseek
import json
import re

READER_SYSTEM_PROMPT = """你是一位资深的网文读者，热爱各种类型的小说。
请以真实读者的身份阅读小说章节，并从读者体验的角度给出评分和反馈。

【评分维度】
1. 代入感 (engagement) - 能否沉浸进故事？
2. 节奏感 (pacing) - 张弛有度还是拖沓/仓促？
3. 期待感 (anticipation) - 看完这章想不想看下一章？
4. 情感共鸣 (emotional_impact) - 有没有被打动？
5. 信息密度 (info_density) - 信息量适中还是一头雾水？
6. 阅读疲劳度 (fatigue) - 自然流畅还是读着累？

每项 1-10 分。高分意味着这方面做得好。

【输出格式】
必须返回 JSON 格式：
{
  "scores": {"engagement": 8, "pacing": 7, "anticipation": 9, "emotional_impact": 6, "info_density": 7, "fatigue": 8},
  "comments": "总体评语…",
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "would_continue": true/false
}"""


class ReaderService:

    async def simulate_read(self, chapter_id: int, db: Session) -> Dict[str, Any]:
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not chapter:
            return {"status": "error", "message": "章节不存在"}

        if not chapter.content:
            return {
                "status": "ok",
                "scores": {},
                "comments": "章节内容为空，无法阅读",
                "strengths": [],
                "weaknesses": [],
                "would_continue": False,
            }

        volume = db.query(Volume).filter(
            Volume.id == chapter.volume_id).first()

        user_prompt = (
            f"请以读者的身份阅读以下章节，并给出评分和反馈。\n\n"
            f"【小说背景】第{chapter.chapter_order}章 - 「{chapter.title}」\n"
            f"{'所属：' + volume.title if volume else ''}\n\n"
            f"【正文】\n{chapter.content[:8000]}"
        )

        result = await call_deepseek(
            READER_SYSTEM_PROMPT, user_prompt, temperature=0.5, max_tokens=2048)

        report = self._parse_json(result) if result else {}
        if not report:
            report = {
                "scores": {
                    "engagement": 0,
                    "pacing": 0,
                    "anticipation": 0,
                    "emotional_impact": 0,
                    "info_density": 0,
                    "fatigue": 0,
                },
                "comments": "AI 阅读服务异常",
                "strengths": [],
                "weaknesses": [],
                "would_continue": False,
            }

        # 保存到章节
        chapter.reader_report = json.dumps(report, ensure_ascii=False)
        db.commit()

        return {
            "status": "ok",
            **report,
        }

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return {}
