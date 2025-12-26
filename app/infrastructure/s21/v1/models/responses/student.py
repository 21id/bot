from app.domain.user.status import StudentStatus
from app.infrastructure.s21.v1.models.responses.campus import ParticipantCampusV1DTO

from pydantic import BaseModel


class ParticipantV1DTO(BaseModel):
    """Student API model."""
    login: str # bibikov-lukyan

    # Can be None if student is blocked (or other reason, somehow)
    className: str | None = None # ADONIS
    parallelName: str | None = None # Core program / I_CAMPUS_INTENSIVE-ID_DDMMYY

    # Exp and levels
    expValue: int # 100
    level: int # 0
    expToNextLevel: int # 399

    status: StudentStatus # Active
    campus: ParticipantCampusV1DTO # Campus DTO
