from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..schemas import ChapterCreate, ChapterUpdate, ChapterOut
from ..models import Volume, Chapter

router = APIRouter(prefix="/api/chapters")


def _chapter_out(c: Chapter) -> ChapterOut:
    project_id = c.volume.project_id if c.volume else 0
    return ChapterOut(
        id=c.id,
        volume_id=c.volume_id,
        project_id=project_id,
        title=c.title,
        chapter_order=c.chapter_order,
        skeleton=c.skeleton,
        content=c.content,
        writing_notes=c.writing_notes,
        status=c.status,
        creator_assessment=c.creator_assessment_dict,
        supervisor_report=c.supervisor_report_dict,
        reader_report=c.reader_report_dict,
        version=c.version,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post("/{volume_id}", response_model=ChapterOut, status_code=201)
async def create_chapter(volume_id: int, chapter: ChapterCreate, db: Session = Depends(get_db)):
    volume = db.query(Volume).filter(Volume.id == volume_id).first()
    if not volume:
        raise HTTPException(404, "Volume not found")
    db_chapter = Chapter(volume_id=volume_id, **chapter.model_dump())
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return _chapter_out(db_chapter)


@router.get("/{chapter_id}", response_model=ChapterOut)
async def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).options(
        selectinload(Chapter.volume)
    ).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(404, "Chapter not found")
    return _chapter_out(chapter)


@router.put("/{chapter_id}", response_model=ChapterOut)
async def update_chapter(chapter_id: int, update: ChapterUpdate, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(404, "Chapter not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        if field in ("creator_assessment", "supervisor_report", "reader_report"):
            if value is not None:
                setattr(chapter, f"{field}_dict", value)
        else:
            setattr(chapter, field, value)
    db.commit()
    db.refresh(chapter)
    return _chapter_out(chapter)


@router.delete("/{chapter_id}")
async def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """删除章节"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(404, "Chapter not found")
    db.delete(chapter)
    db.commit()
    return {"detail": "deleted"}
