"""Enums for database models."""

import enum


class GradeValue(int, enum.Enum):
    """Grade values: 1 (best) to 5 (worst)."""
    EXCELLENT = 1
    GOOD = 2
    SATISFACTORY = 3
    POOR = 4
    FAIL = 5


class CloseReason(str, enum.Enum):
    """Reason why grade topic was closed."""
    RESOLVED = "resolved"  # Student learned the topic
    SKIPPED = "skipped"  # Decided to skip this topic
    NO_LONGER_RELEVANT = "no_longer_relevant"  # Topic is not relevant anymore


class BonusTaskStatus(str, enum.Enum):
    """Status of bonus task."""
    PENDING = "pending"  # Task created, waiting for completion
    COMPLETED = "completed"  # Student completed the task
    CANCELLED = "cancelled"  # Task was cancelled


class HomeworkStatus(str, enum.Enum):
    """Status of homework."""
    PENDING = "pending"  # Not done yet
    DONE = "done"  # Completed
    OVERDUE = "overdue"  # Deadline passed, not completed


class TopicReviewStatus(str, enum.Enum):
    """Status of topic review."""
    PENDING = "pending"  # Topic needs reinforcement
    REINFORCED = "reinforced"  # Topic was reinforced through bonus tasks


class ChannelType(str, enum.Enum):
    """Communication channel type (matches OpenClaw channel names)."""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    SLACK = "slack"
    SIGNAL = "signal"
    IMESSAGE = "imessage"
    MSTEAMS = "msteams"
    MATRIX = "matrix"


class FamilyRole(str, enum.Enum):
    """Role of a family member in the learning system."""
    ADMIN = "admin"  # System administrator (e.g. parent who manages everything)
    PARENT = "parent"  # Parent without admin rights
    STUDENT = "student"  # The child being tracked
    TUTOR = "tutor"  # Teaches specific subjects (e.g. grandma, aunt)
    RELATIVE = "relative"  # Other family members
