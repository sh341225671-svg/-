"""分卷路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict

from ..database import get_db
from ..models import Volume, Chapter

router = APIRouter(prefix="/api/volumes")


@router.put("/{volume_id}")
async def update_volume(volume_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    volume = db.query(Volume).filter(Volume.id == volume_id).first()
    if not volume:
        raise HTTPException(404, "Volume not found")
    for field, value in body.items():
        if hasattr(volume, field):
            setattr(volume, field, value)
    db.commit()
    db.refresh(volume)
    return {
        "id": volume.id,
        "title": volume.title,
        "vol_order": volume.vol_order,
        "summary": volume.summary,
        "outline": volume.outline,
        "status": volume.status,
    }


@router.delete("/{volume_id}")
async def delete_volume(volume_id: int, db: Session = Depends(get_db)):
    """删除分卷及其下所有章节"""
    volume = db.query(Volume).filter(Volume.id == volume_id).first()
    if not volume:
        raise HTTPException(404, "Volume not found")
    db.query(Chapter).filter(Chapter.volume_id == volume_id).delete()
    db.delete(volume)
    db.commit()
    return {"detail": "deleted"}
