from pydantic import Field, BaseModel, AliasChoices


class ParticipantCampusV1DTO(BaseModel):
    """Campus API model."""

    # ff19a3a7-12f5-4332-9582-624519c3eaea
    uuid: str = Field(validation_alias=AliasChoices("uuid", "id"))
    # example: Hogwarts
    short_name: str = Field(validation_alias=AliasChoices(
        "short_name", "shortName"))
