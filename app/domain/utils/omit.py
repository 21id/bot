from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, model_serializer


@dataclass
class OmitIfNone:
    """Field marker: omit field from serialization when its value is None."""


class BaseModel_(BaseModel):
    """Base model honouring ``OmitIfNone`` field markers on serialization."""

    @model_serializer
    def _serialize(self) -> dict[str, Any]:
        omit_if_none_fields = {
            k
            for k, v in type(self).model_fields.items()
            if any(isinstance(m, OmitIfNone) for m in v.metadata)
        }

        return {k: v for k, v in self if k not in omit_if_none_fields or v is not None}
