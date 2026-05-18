import json
from datetime import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    memory_level: Mapped[str] = mapped_column(nullable=False)
    key: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    embedding: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def content_dict(self):
        return json.loads(self.content) if self.content else {}

    @content_dict.setter
    def content_dict(self, value):
        self.content = json.dumps(value, ensure_ascii=False)


class StyleFingerprint(Base):
    __tablename__ = "style_fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id"), nullable=True
    )
    mean_sentence_len: Mapped[float] = mapped_column(default=0.0)
    sentence_len_variance: Mapped[float] = mapped_column(default=0.0)
    metaphor_density: Mapped[float] = mapped_column(default=0.0)
    narrative_distance: Mapped[str] = mapped_column(nullable=True)
    dialogue_ratio: Mapped[float] = mapped_column(default=0.0)
    emotional_intensity: Mapped[float] = mapped_column(default=0.0)
    baseline_diff: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    @property
    def baseline_diff_dict(self):
        return json.loads(self.baseline_diff) if self.baseline_diff else {}

    @baseline_diff_dict.setter
    def baseline_diff_dict(self, value):
        self.baseline_diff = json.dumps(value, ensure_ascii=False)
