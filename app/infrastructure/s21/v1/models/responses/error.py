from pydantic import BaseModel


class ErrorResponseDTO(BaseModel):
    """Error response from API."""

    status: int
    exceptionUUID: str
    code: str
    message: str
