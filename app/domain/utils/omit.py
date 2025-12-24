from dataclasses import dataclass

from pydantic import BaseModel, model_serializer


@dataclass
class OmitIfNone:
    pass

class BaseModel_(BaseModel):
    @model_serializer
    def _serialize(self):
        omit_if_none_fields = {
            k
            for k, v in self.model_fields.items()
            if any(isinstance(m, OmitIfNone) for m in v.metadata)
        }

        return {k: v for k, v in self if k not in omit_if_none_fields or v is not None}
