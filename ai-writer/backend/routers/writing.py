"""写作和审校路由 - 集成数据库读写"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict

from ..database import get_db
from ..models import Chapter
from ..services.creator import CreatorService
from ..services.supervisor import SupervisorService
from ..services.reader import ReaderService

router = APIRouter(prefix="/api/writing")


@router.post("/auto")
async def auto_write(body: Dict[str, Any], db: Session = Depends(get_db)):
    svc = CreatorService()
    result = await svc.auto_write(
        project_id=body.get("project_id", 0),
        chapter_id=body.get("chapter_id", 0),
        db=db,
        request=body.get("request"),
    )
    return result


@router.post("/semi/skeleton")
async def fill_skeleton(body: Dict[str, Any], db: Session = Depends(get_db)):
    svc = CreatorService()
    result = await svc.fill_skeleton(
        skeleton=body.get("skeleton", ""),
        context=body.get("context", {}),
        db=db,
    )
    return result


@router.post("/semi/rewrite")
async def rewrite_section(body: Dict[str, Any], db: Session = Depends(get_db)):
    svc = CreatorService()
    content = body.get("content", "")
    result = await svc.rewrite_section(
        content=content,
        instruction=body.get("instruction", ""),
    )
    # 如果返回了新内容且前端传了章节 ID，把修改保存到 DB
    chapter_id = body.get("chapter_id")
    rewritten = result.get("rewritten")
    if chapter_id and rewritten and rewritten != content:
        chapter = db.query(Chapter).filter(
            Chapter.id == chapter_id).first()
        if chapter and chapter.content:
            chapter.content = chapter.content.replace(content, rewritten)
            db.commit()
    return result


@router.post("/review/{chapter_id}")
async def review_chapter(chapter_id: int, db: Session = Depends(get_db)):
    svc = SupervisorService()
    result = await svc.review(chapter_id, db=db)
    return result


@router.post("/read/{chapter_id}")
async def simulate_read(chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(404, "Chapter not found")
    svc = ReaderService()
    result = await svc.simulate_read(chapter_id, db=db)
    return result


@router.post("/pipeline/{chapter_id}")
async def run_pipeline(chapter_id: int, db: Session = Depends(get_db)):
    """全自动流水线：创作 → 督查 → 读者 → 终端审核"""
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(404, "Chapter not found")

    volume = chapter.volume
    if not volume:
        raise HTTPException(400, "Chapter has no volume")

    project_id = volume.project_id

    # Step 1: 自动创作
    creator = CreatorService()
    write_result = await creator.auto_write(project_id, chapter_id, db)
    if not write_result.get("content"):
        return {"status": "failed", "step": "writing", "detail": "创作失败"}

    # Step 2: 督查审校
    supervisor = SupervisorService()
    review_result = await supervisor.review(chapter_id, db)

    # Step 3: 读者模拟
    reader = ReaderService()
    read_result = await reader.simulate_read(chapter_id, db)

    # Step 4: 终端审核
    approve_result = await supervisor.final_approve(chapter_id, db)

    return {
        "status": "completed",
        "writing": write_result,
        "review": review_result,
        "reading": read_result,
        "approval": approve_result,
    }
