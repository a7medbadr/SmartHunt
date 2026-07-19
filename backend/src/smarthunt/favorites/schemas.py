from pydantic import BaseModel, Field


class FavoriteJobCreate(BaseModel):
    job_id: int = Field(..., description="ID of the target job")


class FavoriteJobResponse(BaseModel):
    id: int
    job_id: int

    class Config:
        from_attributes = True
