import json
from datetime import datetime
from sqlalchemy import ForeignKey, Text, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


# 项目与 Agent 的多对多关联表
project_agents = Table(
    "project_agents",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
    Column("agent_config_id", ForeignKey("agent_configs.id"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(nullable=False)
    genre: Mapped[str] = mapped_column(nullable=False)
    core_theme: Mapped[str] = mapped_column(Text, nullable=False)
    world_setting: Mapped[str] = mapped_column(Text, nullable=True)
    whole_book_outline: Mapped[str] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str] = mapped_column(nullable=True)
    word_goal: Mapped[int] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="draft")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    volumes = relationship("Volume", back_populates="project")
    characters = relationship("Character", back_populates="project")
    agent_configs = relationship("AgentConfig", secondary=project_agents, back_populates="projects")

    @property
    def world_setting_dict(self):
        if not self.world_setting:
            return {}
        try:
            return json.loads(self.world_setting)
        except (json.JSONDecodeError, TypeError):
            return str(self.world_setting)

    @world_setting_dict.setter
    def world_setting_dict(self, value):
        self.world_setting = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value


class Volume(Base):
    __tablename__ = "volumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    vol_order: Mapped[int] = mapped_column(nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    outline: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="draft")

    project = relationship("Project", back_populates="volumes")
    chapters = relationship("Chapter", back_populates="volume")


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    volume_id: Mapped[int] = mapped_column(
        ForeignKey("volumes.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    chapter_order: Mapped[int] = mapped_column(nullable=False)
    skeleton: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    writing_notes: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(default="draft")
    creator_assessment: Mapped[str] = mapped_column(Text, nullable=True)
    supervisor_report: Mapped[str] = mapped_column(Text, nullable=True)
    reader_report: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    volume = relationship("Volume", back_populates="chapters")

    @property
    def creator_assessment_dict(self):
        return (
            json.loads(self.creator_assessment)
            if self.creator_assessment
            else {}
        )

    @creator_assessment_dict.setter
    def creator_assessment_dict(self, value):
        self.creator_assessment = json.dumps(value, ensure_ascii=False)

    @property
    def supervisor_report_dict(self):
        return (
            json.loads(self.supervisor_report)
            if self.supervisor_report
            else {}
        )

    @supervisor_report_dict.setter
    def supervisor_report_dict(self, value):
        self.supervisor_report = json.dumps(value, ensure_ascii=False)

    @property
    def reader_report_dict(self):
        return (
            json.loads(self.reader_report) if self.reader_report else {}
        )

    @reader_report_dict.setter
    def reader_report_dict(self, value):
        self.reader_report = json.dumps(value, ensure_ascii=False)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    # 八维角色塑造
    gender: Mapped[str] = mapped_column(nullable=True)
    age: Mapped[str] = mapped_column(nullable=True)
    personality: Mapped[str] = mapped_column(Text, nullable=True)
    family_background: Mapped[str] = mapped_column(Text, nullable=True)
    occupation: Mapped[str] = mapped_column(nullable=True)
    values: Mapped[str] = mapped_column(Text, nullable=True)
    special_traits: Mapped[str] = mapped_column(Text, nullable=True)
    character_status: Mapped[str] = mapped_column(default="active")
    # 原有字段保持兼容
    profile: Mapped[str] = mapped_column(Text, nullable=True)
    relationships: Mapped[str] = mapped_column(Text, nullable=True)
    first_appearance: Mapped[int] = mapped_column(nullable=True)
    arc: Mapped[str] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="characters")

    @property
    def char_dict(self):
        """返回八维角色塑造的结构化字典"""
        return {
            "gender": self.gender,
            "age": self.age,
            "personality": self.personality,
            "family_background": self.family_background,
            "occupation": self.occupation,
            "values": self.values,
            "special_traits": self.special_traits,
            "character_status": self.character_status,
        }

    @property
    def profile_dict(self):
        return json.loads(self.profile) if self.profile else {}

    @profile_dict.setter
    def profile_dict(self, value):
        self.profile = json.dumps(value, ensure_ascii=False)

    @property
    def relationships_dict(self):
        return json.loads(self.relationships) if self.relationships else {}

    @relationships_dict.setter
    def relationships_dict(self, value):
        self.relationships = json.dumps(value, ensure_ascii=False)

    @property
    def arc_dict(self):
        return json.loads(self.arc) if self.arc else {}

    @arc_dict.setter
    def arc_dict(self, value):
        self.arc = json.dumps(value, ensure_ascii=False)
