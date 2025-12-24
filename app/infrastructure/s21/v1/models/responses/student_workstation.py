from pydantic import BaseModel


class ParticipantWorkstationV1DTO(BaseModel):
    """Student workstation (campus) model."""
    clusterId: int # 854
    clusterName: str # Ocean

    row: str # a
    number: int # 24
