from typing import Optional, Annotated
from datetime import datetime

from app.domain.campus.campus import Campus
from app.domain.utils.omit import BaseModel_, OmitIfNone
from app.domain.utils.object_id import PyObjectId

from pydantic import model_validator, Field, ConfigDict


class User(BaseModel_):
    """User model."""

    model_config = ConfigDict(
        populate_by_name=True,  # Allows filling by alias, while using local name
        arbitrary_types_allowed=True,  # Allows Pydantic to accept ObjectId objects
    )

    # TODO: stop using aliases and move to separate DB model
    id: Annotated[str | PyObjectId, OmitIfNone()] = Field(alias="_id", default=None)

    # School 21 student information
    nickname: str = Field(alias="login")
    wave_name: str = Field(alias="className")
    # Core program or intensive (I_'CAMPUS'_'INTENSIVE-ID'_'DDMMYY')
    parallel: str = Field(alias="parallelName")
    campus: Campus

    is_verified: bool

    # Mandatory fields for verified user
    telegram_id: int | None = None

    # Optional fields for verified user
    name: Optional[str] = None
    surname: Optional[str] = None
    phone_number: Optional[str] = None
    personal_email: Optional[str] = None

    # Invite one-time-code
    invite_otp: Annotated[str | None, OmitIfNone()] = None

    created_at: datetime = Field(default=datetime.now())
    verified_at: datetime = Field(default=datetime.now())

    @model_validator(mode="after")
    def validate_verified(self) -> "User":
        """Validation of verified user model.

        :return: User
        """
        mandatory_fields = [self.telegram_id]

        if self.is_verified and not all(mandatory_fields):
            raise ValueError("Field telegram_id is required when user is verified")
        return self
