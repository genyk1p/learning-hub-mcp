"""FamilyMember model - family members participating in the learning system."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import FamilyRole

if TYPE_CHECKING:
    from learning_hub.models.gateway import Gateway


class FamilyMember(Base, TimestampMixin):
    """
    A family member in the learning system.

    Can be a student, parent, admin, tutor, or relative.
    Each member can have multiple gateways (Telegram, etc.) for communication.
    Only one student is allowed in the system (enforced by unique constraint).
    """

    __tablename__ = "family_members"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Display name (how the agent should address them)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Full legal name (optional)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Role in the learning system
    role: Mapped[FamilyRole] = mapped_column(nullable=False)

    # Has sudo/admin access to system configuration
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Is the tracked student (whose grades/homework are managed)
    is_student: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Free text notes for the agent
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    gateways: Mapped[list["Gateway"]] = relationship(
        "Gateway", back_populates="family_member", passive_deletes=True
    )

    # Constraints
    __table_args__ = (
        # Student cannot be admin
        CheckConstraint(
            "NOT (is_student = 1 AND is_admin = 1)",
            name="check_student_not_admin",
        ),
        # Only one student allowed in the system (partial unique index)
        Index(
            "uq_single_student",
            "is_student",
            unique=True,
            sqlite_where=text("is_student = 1"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FamilyMember(id={self.id}, name={self.name!r}, "
            f"role={self.role.value}, is_admin={self.is_admin}, "
            f"is_student={self.is_student})>"
        )
