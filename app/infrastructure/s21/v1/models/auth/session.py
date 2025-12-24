from pydantic import BaseModel


class Session(BaseModel):
    """OIDC session."""

    access_token: str
    refresh_token: str
