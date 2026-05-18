"""记忆系统服务 - L1-L5 记忆的读写和管理"""
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from ..models import Project, Chapter, Character, Volume, MemoryRecord, StyleFingerprint
import json


class MemoryService:

    def load_context(self, project_id: int, db: Session) -> Dict[str, Any]:
        """加载项目全貌记忆 L1-L5，返回结构化的上下文字典"""
        context = {"L1": {}, "L2": {}, "L3": {}, "L4": {}, "L5": []}

        project = db.query(Project).filter(
            Project.id == project_id).first()
        if not project:
            return context

        # L1 世界观
        context["L1"] = {
            "world_setting": project.world_setting_dict,
            "core_theme": project.core_theme,
            "genre": project.genre,
        }

        # L2 角色库
        characters = db.query(Character).filter(
            Character.project_id == project_id).all()
        context["L2"]["characters"] = [
            {
                "name": c.name,
                "role": c.role,
                "profile": c.profile_dict,
                "arc": c.arc_dict,
                "relationships": c.relationships_dict,
            }
            for c in characters
        ]

        # L3 故事线 + L5 章节记忆
        volumes = db.query(Volume).filter(
            Volume.project_id == project_id).order_by(Volume.vol_order).all()
        all_chapters = []
        for v in volumes:
            chs = db.query(Chapter).filter(
                Chapter.volume_id == v.id).order_by(Chapter.chapter_order).all()
            for ch in chs:
                all_chapters.append(ch)
                if ch.content:
                    context["L5"].append({
                        "chapter_id": ch.id,
                        "title": ch.title,
                        "order": ch.chapter_order,
                        "summary": ch.content[:300],
                        "status": ch.status,
                    })

        context["L3"]["total_chapters"] = len(all_chapters)
        context["L3"]["written_chapters"] = len(
            [c for c in all_chapters if c.content])

        # L4 风格基线
        baseline = db.query(MemoryRecord).filter(
            MemoryRecord.project_id == project_id,
            MemoryRecord.key == "style_baseline"
        ).first()
        if baseline:
            try:
                context["L4"]["baseline"] = json.loads(
                    baseline.content) if baseline.content else {}
            except json.JSONDecodeError:
                context["L4"]["baseline"] = {}

        return context

    def update_chapter_memory(self, project_id: int, chapter_id: int, db: Session) -> None:
        """更新 L5 章节记忆"""
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not chapter or not chapter.content:
            return

        summary = chapter.content[:500]
        existing = db.query(MemoryRecord).filter(
            MemoryRecord.project_id == project_id,
            MemoryRecord.key == f"chapter_{chapter_id}_summary"
        ).first()

        data = json.dumps({
            "summary": summary,
            "chapter_order": chapter.chapter_order,
            "title": chapter.title,
            "status": chapter.status,
            "version": chapter.version,
        }, ensure_ascii=False)

        if existing:
            existing.content = data
        else:
            db.add(MemoryRecord(
                project_id=project_id,
                memory_level="L5",
                key=f"chapter_{chapter_id}_summary",
                content=data,
            ))
        db.commit()

    def compute_style_fingerprint(self, chapter_id: int, db: Session) -> Dict[str, Any]:
        """计算章节的风格指纹"""
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not chapter or not chapter.content:
            return {}

        text = chapter.content
        sentences = [s.strip() for s in text.replace(
            "。", ".").replace("！", ".").replace("？", ".").replace("\n", ".").split(".") if s.strip()]

        if not sentences:
            return {}

        sentence_lens = [len(s) for s in sentences]
        total_chars = len(text.replace("\n", "").replace(" ", ""))
        # 粗略估算比喻密度
        metaphor_keywords = [
            "如", "像", "仿佛", "宛如", "犹如", "似的", "一般", "般的"]
        metaphor_count = sum(text.count(k) for k in metaphor_keywords)
        metaphor_density = metaphor_count / max(total_chars / 1000, 1)

        # 对话占比（中文引号内字符）
        dialogue_chars = 0
        in_quote = False
        for char in text:
            if char in "「『""":
                in_quote = True
            elif char in "」』""":
                in_quote = False
                dialogue_chars += 1
            elif in_quote:
                dialogue_chars += 1

        mean_len = sum(sentence_lens) / len(sentence_lens)
        variance = sum((l - mean_len) ** 2 for l in sentence_lens) / \
            len(sentence_lens)

        fingerprint = {
            "mean_sentence_len": round(mean_len, 2),
            "sentence_len_variance": round(variance, 2),
            "metaphor_density": round(metaphor_density, 4),
            "dialogue_ratio": round(dialogue_chars / max(total_chars, 1), 4),
            "emotional_intensity": 0.0,
            "total_chars": total_chars,
        }

        # 保存到数据库
        volume = chapter.volume
        project_id = volume.project_id if volume else 0

        existing = db.query(StyleFingerprint).filter(
            StyleFingerprint.chapter_id == chapter_id
        ).first()
        if existing:
            existing.mean_sentence_len = fingerprint["mean_sentence_len"]
            existing.sentence_len_variance = fingerprint["sentence_len_variance"]
            existing.metaphor_density = fingerprint["metaphor_density"]
            existing.dialogue_ratio = fingerprint["dialogue_ratio"]
        else:
            db.add(StyleFingerprint(
                project_id=project_id,
                chapter_id=chapter_id,
                mean_sentence_len=fingerprint["mean_sentence_len"],
                sentence_len_variance=fingerprint["sentence_len_variance"],
                metaphor_density=fingerprint["metaphor_density"],
                dialogue_ratio=fingerprint["dialogue_ratio"],
            ))
        db.commit()

        return fingerprint

    def compare_style(self, chapter_id: int, db: Session) -> Dict[str, Any]:
        """将章节的风格与项目基线对比，返回漂移检测结果"""
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if not chapter:
            return {}

        volume = chapter.volume
        if not volume:
            return {}
        project_id = volume.project_id

        current = self.compute_style_fingerprint(chapter_id, db)
        if not current:
            return {}

        # 计算基线（所有历史章节的平均值）
        all_fps = db.query(StyleFingerprint).filter(
            StyleFingerprint.project_id == project_id,
            StyleFingerprint.chapter_id != chapter_id,
        ).all()

        if not all_fps:
            return {"is_baseline": True,
                "fingerprint": current, "drift_warnings": []}

        baseline = {
            "mean_sentence_len": sum(
                fp.mean_sentence_len for fp in all_fps) / len(all_fps),
            "metaphor_density": sum(
                fp.metaphor_density for fp in all_fps) / len(all_fps),
            "dialogue_ratio": sum(
                fp.dialogue_ratio for fp in all_fps) / len(all_fps),
        }

        warnings = []
        metrics = [
            ("mean_sentence_len", "句长均值"),
            ("metaphor_density", "比喻密度"),
            ("dialogue_ratio", "对话占比"),
        ]
        for key, label in metrics:
            if baseline[key] > 0:
                ratio = current[key] / baseline[key]
                if ratio > 1.15:
                    warnings.append(
                        f"{label} 超出基线 +{round((ratio-1)*100)}%")
                elif ratio < 0.85:
                    warnings.append(
                        f"{label} 低于基线 -{round((1-ratio)*100)}%")

        return {
            "is_baseline": False,
            "current": current,
            "baseline": {k: round(v, 4) for k, v in baseline.items()},
            "drift_warnings": warnings,
        }
