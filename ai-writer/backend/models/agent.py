import json
from datetime import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_type: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(default="deepseek-v4-flash")
    parameters: Mapped[str] = mapped_column(Text, nullable=True)
    capabilities: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    logs = relationship("AgentLog", back_populates="agent_config")
    projects = relationship("Project", secondary="project_agents", back_populates="agent_configs", overlaps="volumes,characters")

    @property
    def parameters_dict(self):
        return json.loads(self.parameters) if self.parameters else {}

    @parameters_dict.setter
    def parameters_dict(self, value):
        self.parameters = json.dumps(value, ensure_ascii=False)

    @property
    def capabilities_list(self):
        return json.loads(self.capabilities) if self.capabilities else []

    @capabilities_list.setter
    def capabilities_list(self, value):
        self.capabilities = json.dumps(value, ensure_ascii=False)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_config_id: Mapped[int] = mapped_column(
        ForeignKey("agent_configs.id"), nullable=False
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=True)
    response: Mapped[str] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(default=0)
    latency_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    agent_config = relationship("AgentConfig", back_populates="logs")
