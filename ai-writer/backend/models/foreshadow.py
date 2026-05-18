from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Foreshadow(Base):
    __tablename__ = "foreshadows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    foreshadow_type: Mapped[str] = mapped_column(nullable=False)
    laid_at_chapter: Mapped[int] = mapped_column(nullable=False)
    expected_payoff_chapter: Mapped[int] = mapped_column(nullable=False)
    actual_payoff_chapter: Mapped[int] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="open")
    alert_triggered: Mapped[bool] = mapped_column(default=False)
