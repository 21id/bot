from pydantic import BaseModel


class Credentials(BaseModel):
    """School 21 login credentials."""

    login: str
    password: str
