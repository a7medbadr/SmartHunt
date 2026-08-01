from pydantic import BaseModel, ConfigDict, Field

from smarthunt.api.schemas.job import JobResponse


class FavoriteJobCreate(BaseModel):
    job_id: int = Field(..., description="ID of the target job")


class FavoriteJobResponse(BaseModel):
    id: int
    job_id: int
    job: JobResponse | None = None

    model_config = ConfigDict(from_attributes=True)
