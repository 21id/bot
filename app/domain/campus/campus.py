from typing import Optional

from app.domain.utils.omit import BaseModel_


class Campus(BaseModel_):
    """Campus model."""

    id: Optional[int] = None
    uuid: Optional[str] = None
    short_name: str
    full_name: Optional[str] = None
