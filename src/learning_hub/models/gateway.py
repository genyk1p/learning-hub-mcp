"""Gateway model - communication channels for family members."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from learning_hub.models.base import Base, TimestampMixin
from learning_hub.models.enums import ChannelType

if TYPE_CHECKING:
    from learning_hub.models.family_member import FamilyMember


class Gateway(Base, TimestampMixin):
    """
    A communication channel identity for a family member.

    Maps a family member to their identity on a specific platform
    (Telegram, WhatsApp, Discord, etc.). One member can have multiple
    gateways (e.g. Telegram + WhatsApp).

    The (channel, channel_uid) pair is unique — used for lookup
    "who is sending this message" by the agent.
    """

    __tablename__ = "gateways"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Which family member this gateway belongs to
    family_member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Platform type: telegram, whatsapp, discord, etc.
    channel: Mapped[ChannelType] = mapped_column(nullable=False)

    # User's identifier on this platform (Telegram ID, phone number, username, etc.)
    channel_uid: Mapped[str] = mapped_column(String(100), nullable=False)

    # Optional label: "personal", "work", etc.
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Default channel for sending messages to this member
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    family_member: Mapped["FamilyMember"] = relationship(
        "FamilyMember", back_populates="gateways"
    )

    # Constraints
    __table_args__ = (
        # Same channel_uid on the same channel can't belong to two different members
        UniqueConstraint("channel", "channel_uid", name="uq_channel_uid"),
        # Only one default gateway per family member
        Index(
            "uq_default_per_member",
            "family_member_id",
            unique=True,
            sqlite_where=text("is_default = 1"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Gateway(id={self.id}, channel={self.channel!r}, "
            f"channel_uid={self.channel_uid!r}, member_id={self.family_member_id})>"
        )
