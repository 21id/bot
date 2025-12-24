from enum import Enum


class StudentStatus(str, Enum):
    """Student possible statuses."""

    ACTIVE = "ACTIVE"
    TEMPORARY_BLOCKING = "TEMPORARY_BLOCKING"
    EXPELLED = "EXPELLED"
    BLOCKED = "BLOCKED"
    FROZEN = "FROZEN"
    STUDY_COMPLETED = "STUDY_COMPLETED"
