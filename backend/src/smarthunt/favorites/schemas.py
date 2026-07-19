from pydantic import BaseModel, ConfigDict, Field


class FavoriteJobCreate(BaseModel):
    job_id: int = Field(..., description="ID of the target job")


class FavoriteJobResponse(BaseModel):
    id: int
    job_id: int

    model_config = ConfigDict(from_attributes=True)
