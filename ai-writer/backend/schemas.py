"""Pydantic 模式定义"""
from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel


# ====== 项目 ======

class ProjectCreate(BaseModel):
    title: str
    genre: str = "其他"
    core_theme: str = ""
    world_setting: Optional[Any] = None  # 接受 str 或 Dict
    whole_book_outline: Optional[str] = None
    agent_ids: List[int] = []
    target_audience: Optional[str] = None
    word_goal: Optional[int] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    core_theme: Optional[str] = None
    world_setting: Optional[Any] = None  # 接受 str 或 Dict
    whole_book_outline: Optional[str] = None
    agent_ids: Optional[List[int]] = None
    target_audience: Optional[str] = None
    word_goal: Optional[int] = None
    status: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    title: str
    genre: str
    core_theme: str
    world_setting: Optional[Any] = None  # 可能是 str 或 Dict
    whole_book_outline: Optional[str] = None
    agent_ids: List[int] = []
    target_audience: Optional[str] = None
    word_goal: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    volumes: List["VolumeOut"] = []
    characters: List["CharacterOut"] = []

    model_config = {"from_attributes": True}


# ====== 分卷 ======

class VolumeCreate(BaseModel):
    title: str
    vol_order: int
    summary: Optional[str] = None
    outline: Optional[str] = None

class VolumeOut(BaseModel):
    id: int
    project_id: int
    title: str
    vol_order: int
    summary: Optional[str] = None
    outline: Optional[str] = None
    status: str
    chapters: List["ChapterOut"] = []

    model_config = {"from_attributes": True}


# ====== 章节 ======

class ChapterCreate(BaseModel):
    title: str
    chapter_order: int
    skeleton: Optional[str] = None
    content: Optional[str] = None
    writing_notes: Optional[str] = None

class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    skeleton: Optional[str] = None
    content: Optional[str] = None
    writing_notes: Optional[str] = None
    status: Optional[str] = None
    creator_assessment: Optional[Dict[str, Any]] = None
    supervisor_report: Optional[Dict[str, Any]] = None
    reader_report: Optional[Dict[str, Any]] = None

class ChapterOut(BaseModel):
    id: int
    volume_id: int
    project_id: int = 0
    title: str
    chapter_order: int
    skeleton: Optional[str] = None
    content: Optional[str] = None
    writing_notes: Optional[str] = None
    status: str
    creator_assessment: Optional[Dict[str, Any]] = None
    supervisor_report: Optional[Dict[str, Any]] = None
    reader_report: Optional[Dict[str, Any]] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ====== 角色 ======

class CharacterCreate(BaseModel):
    name: str
    role: str
    gender: Optional[str] = None
    age: Optional[str] = None
    personality: Optional[str] = None
    family_background: Optional[str] = None
    occupation: Optional[str] = None
    values: Optional[str] = None
    special_traits: Optional[str] = None
    character_status: str = "active"
    # 兼容原有字段
    profile: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, Any]] = None
    first_appearance: Optional[int] = None
    arc: Optional[Dict[str, Any]] = None

class CharacterOut(BaseModel):
    id: int
    project_id: int
    name: str
    role: str
    gender: Optional[str] = None
    age: Optional[str] = None
    personality: Optional[str] = None
    family_background: Optional[str] = None
    occupation: Optional[str] = None
    values: Optional[str] = None
    special_traits: Optional[str] = None
    character_status: str = "active"
    # 兼容原有字段
    profile: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, Any]] = None
    first_appearance: Optional[int] = None
    arc: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ====== Agent 管理（后台操作口子）======

class AgentConfigCreate(BaseModel):
    agent_type: str  # creator / supervisor / reader
    name: str
    system_prompt: str = ""
    model: str = "deepseek-v4-flash"
    parameters: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None

class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None

class AgentConfigOut(BaseModel):
    id: int
    agent_type: str
    name: str
    is_active: bool
    system_prompt: str
    model: str
    parameters: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ====== 伏笔 ======

class ForeshadowCreate(BaseModel):
    content: str
    foreshadow_type: str
    laid_at_chapter: int
    expected_payoff_chapter: int

class ForeshadowOut(BaseModel):
    id: int
    project_id: int
    chapter_id: Optional[int] = None
    content: str
    foreshadow_type: str
    laid_at_chapter: int
    expected_payoff_chapter: int
    actual_payoff_chapter: Optional[int] = None
    status: str
    alert_triggered: bool

    model_config = {"from_attributes": True}


# ====== 通用 ======

class Message(BaseModel):
    detail: str

class AgentExecuteRequest(BaseModel):
    """向指定 Agent 发送执行请求"""
    agent_type: str  # creator / supervisor / reader
    chapter_id: int
    context: Optional[Dict[str, Any]] = None

class AgentExecuteResponse(BaseModel):
    status: str
    result: Any
    log_id: Optional[int] = None
