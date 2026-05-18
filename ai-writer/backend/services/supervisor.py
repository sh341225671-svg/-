"""AI 督查者服务 - 沈寒版本的严格五步审查"""
from typing import Any, Dict
from sqlalchemy.orm import Session
from ..models import Project, Chapter, Volume, Foreshadow, Character
from ..services.ai import call_deepseek
import json
import re

SUPERVISOR_SYSTEM_PROMPT = """你是一位极其严格的小说编辑，名叫明镜·督查者。
你的工作是按照特定顺序对每一章进行全面审查。

【审查顺序（不可调换）】
Step 1 戏剧必需性（权重 1.5）
  → 这一章删了，故事会不会塌？
  → 每个场景是否承担叙事功能？
  → 如果是过渡章，是否有足够的信息增量？

Step 2 价值转换（权重 1.3）
  → 这一章推动了什么价值的转变？
  → 主角在认知/情感/处境上是否发生了变化？
  → 变化的方向是否符合故事逻辑？

Step 3 冲突真实性（权重 1.2）
  → 冲突是否有内在逻辑？还是为了冲突而冲突？
  → 各方的立场是否站得住脚？
  → 冲突的起因/发展/结果是否合理？

Step 4 一致性（权重 1.0）
  → 角色行为是否符合人设？
  → 世界观规则有没有被打破？
  → 与项目已写章节是否存在矛盾？

Step 5 风格（权重 0.8）
  → 句长分布、叙事节奏是否与之前一致？
  → 是否存在突兀的叙事风格切换？

【输出格式要求】
以 JSON 格式返回，包含 total_score(加权总分), verdict(approved/needs_revision/rejected), checks 数组。
每个 check 包含 step, label, score(1-10), detail, severity(major/minor)."""


class SupervisorService:

    async def review(self, chapter_id: int, db: Session) -> Dict[str, Any]:
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not chapter:
            return {"status": "error", "message": "章节不存在"}

        volume = db.query(Volume).filter(
            Volume.id == chapter.volume_id).first()
        project = db.query(Project).filter(
            Project.id == volume.project_id).first() if volume else None

        if not project or not chapter.content:
            return {"status": "error", "message": "章节内容为空或项目不存在"}

        # 构建审查上下文
        context_parts = [
            f"项目名称：《{project.title}》",
            f"主控思想：{project.core_theme or '未设置'}",
        ]

        # 角色信息
        characters = db.query(Character).filter(
            Character.project_id == project.id).all()
        if characters:
            char_lines = []
            for c in characters:
                profile_str = json.dumps(
                    c.profile_dict, ensure_ascii=False) if c.profile else '未配置'
                char_lines.append(
                    f"  - {c.name}（{c.role}）：人设={profile_str}")
            context_parts.append("角色：\n" + "\n".join(char_lines))

        # 未兑现的伏笔
        open_foreshadows = db.query(Foreshadow).filter(
            Foreshadow.project_id == project.id,
            Foreshadow.status == "open"
        ).all()
        if open_foreshadows:
            f_lines = [
                f"  - 「{f.content}」（铺设于第{f.laid_at_chapter}章，预期回收于第{f.expected_payoff_chapter}章）"
                for f in open_foreshadows
            ]
            context_parts.append("未兑现伏笔：\n" + "\n".join(f_lines))

        context = "\n\n".join(context_parts)

        system_prompt = f"{SUPERVISOR_SYSTEM_PROMPT}\n\n## 项目上下文\n{context}"
        user_prompt = (
            f"请审查第{chapter.chapter_order}章「{chapter.title}」：\n\n"
            f"【正文】\n{chapter.content[:8000]}\n\n"
            f"严格按照五步顺序审查，以 JSON 格式返回：\n"
            f"{{\n"
            f'  "total_score": 加权总分,\n'
            f'  "verdict": "approved|needs_revision|rejected",\n'
            f'  "checks": [\n'
            f'    {{"step": "dramatic_necessity", "label": "戏剧必需性", "score": 8, "detail": "...", "severity": "minor"}},\n'
            f'    {{"step": "value_transformation", "label": "价值转换", "score": 7, "detail": "...", "severity": "minor"}},\n'
            f'    {{"step": "conflict_realism", "label": "冲突真实性", "score": 6, "detail": "...", "severity": "major"}},\n'
            f'    {{"step": "consistency", "label": "一致性", "score": 9, "detail": "...", "severity": "minor"}},\n'
            f'    {{"step": "style", "label": "风格", "score": 8, "detail": "...", "severity": "minor"}}\n'
            f'  ],\n'
            f'  "summary": "总体评语"\n'
            f"}}"
        )

        result = await call_deepseek(
            system_prompt, user_prompt, temperature=0.3, max_tokens=4096)

        # 解析结果
        report_json = self._parse_json(result) if result else None
        if not report_json:
            report_json = {
                "total_score": 0,
                "verdict": "needs_revision",
                "checks": [
                    {"step": "dramatic_necessity", "label": "戏剧必需性",
                        "score": 0, "detail": "AI 审查失败", "severity": "major"}
                ],
                "summary": "AI 审查服务异常，请重试"
            }

        # 保存到章节
        chapter.supervisor_report = json.dumps(
            report_json, ensure_ascii=False)
        db.commit()

        return {
            "status": "ok",
            "report": report_json,
        }

    def _parse_json(self, text: str) -> dict:
        """从 AI 返回文本中提取 JSON"""
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

    async def final_approve(self, chapter_id: int, db: Session) -> Dict[str, Any]:
        """终端审核：汇总督查结果并决定是否通过"""
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not chapter:
            return {"status": "error", "message": "章节不存在"}

        report = chapter.supervisor_report_dict if chapter.supervisor_report else {}
        total_score = report.get("total_score", 0)

        if total_score >= 7:
            chapter.status = "approved"
            verdict = "approved"
        elif total_score >= 4:
            chapter.status = "review"
            verdict = "needs_revision"
        else:
            chapter.status = "rejected"
            verdict = "rejected"

        db.commit()

        return {
            "status": "ok",
            "chapter_id": chapter_id,
            "verdict": verdict,
            "total_score": total_score,
        }
