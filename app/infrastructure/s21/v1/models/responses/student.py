from app.domain.user.status import StudentStatus
from app.infrastructure.s21.v1.models.responses.campus import ParticipantCampusV1DTO

from pydantic import BaseModel


class ParticipantV1DTO(BaseModel):
    """Student API model."""
    login: str # bibikov-lukyan
    className: str # ADONIS

    parallelName: str | None # Core program

    # Exp and levels
    expValue: int # 100
    level: int # 0
    expToNextLevel: int # 399

    status: StudentStatus # Active
    campus: ParticipantCampusV1DTO # Campus DTO
