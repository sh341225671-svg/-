from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    VolumeCreate,
    VolumeOut,
    ChapterOut,
    CharacterCreate,
    CharacterOut,
)
from ..models import Project, Volume, Chapter, Character, AgentConfig

router = APIRouter(prefix="/api/projects")


# ====== helper 转换器 ======

def _chapter_out(c: Chapter) -> ChapterOut:
    return ChapterOut(
        id=c.id,
        volume_id=c.volume_id,
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

def _volume_out(v: Volume) -> VolumeOut:
    return VolumeOut(
        id=v.id,
        project_id=v.project_id,
        title=v.title,
        vol_order=v.vol_order,
        summary=v.summary,
        outline=v.outline,
        status=v.status,
        chapters=[_chapter_out(c) for c in v.chapters],
    )

def _character_out(c: Character) -> CharacterOut:
    return CharacterOut(
        id=c.id,
        project_id=c.project_id,
        name=c.name,
        role=c.role,
        gender=c.gender,
        age=c.age,
        personality=c.personality,
        family_background=c.family_background,
        occupation=c.occupation,
        values=c.values,
        special_traits=c.special_traits,
        character_status=c.character_status,
        profile=c.profile_dict,
        relationships=c.relationships_dict,
        first_appearance=c.first_appearance,
        arc=c.arc_dict,
    )

def _project_out(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        title=p.title,
        genre=p.genre,
        core_theme=p.core_theme,
        world_setting=p.world_setting_dict,
        whole_book_outline=p.whole_book_outline,
        agent_ids=[a.id for a in (p.agent_configs or [])],
        target_audience=p.target_audience,
        word_goal=p.word_goal,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
        volumes=[_volume_out(v) for v in p.volumes],
        characters=[_character_out(c) for c in p.characters],
    )


# ====== Project CRUD ======

@router.get("", response_model=List[ProjectOut])
async def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return [_project_out(p) for p in projects]


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    data = project.model_dump()
    world_setting = data.pop("world_setting", None)
    whole_book_outline = data.pop("whole_book_outline", None)
    agent_ids = data.pop("agent_ids", None)
    db_project = Project(**data)
    if world_setting is not None:
        db_project.world_setting_dict = world_setting
    if whole_book_outline is not None:
        db_project.whole_book_outline = whole_book_outline
    if agent_ids is not None:
        agents = db.query(AgentConfig).filter(AgentConfig.id.in_(agent_ids)).all()
        db_project.agent_configs = agents
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return _project_out(db_project)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return _project_out(project)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: int, update: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    update_data = update.model_dump(exclude_unset=True)
    agent_ids = update_data.pop("agent_ids", None)
    for field, value in update_data.items():
        if field == "world_setting" and value is not None:
            project.world_setting_dict = value
        elif field == "whole_book_outline":
            setattr(project, field, value)
        else:
            setattr(project, field, value)
    if agent_ids is not None:
        agents = db.query(AgentConfig).filter(AgentConfig.id.in_(agent_ids)).all()
        project.agent_configs = agents
    db.commit()
    db.refresh(project)
    return _project_out(project)


@router.delete("", response_model=dict)
async def delete_all_projects(db: Session = Depends(get_db)):
    """清空所有项目（含分卷、章节、角色）"""
    db.query(Chapter).delete()
    db.query(Character).delete()
    db.query(Volume).delete()
    db.query(Project).delete()
    db.commit()
    return {"detail": "all projects deleted"}


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    for volume in project.volumes:
        db.query(Chapter).filter(Chapter.volume_id == volume.id).delete()
    db.query(Volume).filter(Volume.project_id == project_id).delete()
    db.query(Character).filter(Character.project_id == project_id).delete()
    db.delete(project)
    db.commit()
    return {"detail": "deleted"}


# ====== Volume endpoints ======

@router.post("/{project_id}/volumes", response_model=VolumeOut, status_code=201)
async def create_volume(project_id: int, volume: VolumeCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    data = volume.model_dump()
    outline = data.pop("outline", None)
    db_volume = Volume(project_id=project_id, **data)
    if outline is not None:
        db_volume.outline = outline
    db.add(db_volume)
    db.commit()
    db.refresh(db_volume)
    return _volume_out(db_volume)


@router.get("/{project_id}/volumes", response_model=List[VolumeOut])
async def list_volumes(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return [_volume_out(v) for v in project.volumes]


# ====== Character endpoints ======

@router.post("/{project_id}/characters", response_model=CharacterOut, status_code=201)
async def create_character(project_id: int, character: CharacterCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    data = character.model_dump()
    profile = data.pop("profile", None)
    relationships = data.pop("relationships", None)
    arc = data.pop("arc", None)
    char_fields = ["gender", "age", "personality", "family_background",
                   "occupation", "values", "special_traits", "character_status"]
    for cf in char_fields:
        data.pop(cf, None)
    db_char = Character(project_id=project_id, gender=character.gender,
                        age=character.age, personality=character.personality,
                        family_background=character.family_background,
                        occupation=character.occupation, values=character.values,
                        special_traits=character.special_traits,
                        character_status=character.character_status, **data)
    if profile is not None:
        db_char.profile_dict = profile
    if relationships is not None:
        db_char.relationships_dict = relationships
    if arc is not None:
        db_char.arc_dict = arc
    db.add(db_char)
    db.commit()
    db.refresh(db_char)
    return _character_out(db_char)


@router.get("/{project_id}/characters", response_model=List[CharacterOut])
async def list_characters(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return [_character_out(c) for c in project.characters]


@router.put("/{project_id}/characters/{character_id}", response_model=CharacterOut)
async def update_character(project_id: int, character_id: int, character: CharacterCreate, db: Session = Depends(get_db)):
    """更新角色信息"""
    db_char = db.query(Character).filter(
        Character.id == character_id,
        Character.project_id == project_id
    ).first()
    if not db_char:
        raise HTTPException(404, "Character not found")
    data = character.model_dump()
    profile = data.pop("profile", None)
    relationships = data.pop("relationships", None)
    arc = data.pop("arc", None)
    for field, value in data.items():
        if value is not None and hasattr(db_char, field):
            setattr(db_char, field, value)
    if profile is not None:
        db_char.profile_dict = profile
    if relationships is not None:
        db_char.relationships_dict = relationships
    if arc is not None:
        db_char.arc_dict = arc
    db.commit()
    db.refresh(db_char)
    return _character_out(db_char)


@router.delete("/{project_id}/characters/{character_id}")
async def delete_character(project_id: int, character_id: int, db: Session = Depends(get_db)):
    """删除角色"""
    db_char = db.query(Character).filter(
        Character.id == character_id,
        Character.project_id == project_id
    ).first()
    if not db_char:
        raise HTTPException(404, "Character not found")
    db.delete(db_char)
    db.commit()
    return {"detail": "deleted"}
