from typing import Annotated
from bson import ObjectId
from pydantic import BeforeValidator


PyObjectId = Annotated[
    str, BeforeValidator(str),
    BeforeValidator(lambda x: str(x) if isinstance(x, ObjectId) else x)
]
