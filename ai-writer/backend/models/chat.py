"""对话消息模型"""
from datetime import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    agent_config_id: Mapped[int] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(nullable=False)  # user / agent
    agent_type: Mapped[str] = mapped_column(nullable=True)  # creator / supervisor / reader
    section: Mapped[str] = mapped_column(nullable=True, default="general")  # world / outline / characters / chapters / general
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON: {action, target, ...}
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    project = relationship("Project")
