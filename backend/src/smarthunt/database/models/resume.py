from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    stored_path: Mapped[str] = mapped_column(String(512), nullable=False)

    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
