from typing import Optional, Annotated

from app.domain.utils.omit import BaseModel_, OmitIfNone
from app.domain.utils.object_id import PyObjectId

from pydantic import Field


class Chat(BaseModel_):
    """Telegram chat model, for settings of join requests."""

    id: Annotated[str | PyObjectId, OmitIfNone()] = Field(alias="_id", default=None)

    chat_id: int

    # Status for chat join policy
    intensive_allowed: bool = False
    core_allowed: bool = True

    # ID topic, where bot will send links to users
    id_topic_id: Optional[int] = None

    # Description, which user receives on join request approval
    desc_on_join: Optional[str] = None
