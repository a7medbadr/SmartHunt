from pydantic import BaseModel, Field

class DashboardStatisticsResponse(BaseModel):
    jobs: int = Field(default=0, ge=0, description="Total number of available jobs")
    applications: int = Field(default=0, ge=0, description="Total job applications submitted")
    favorites: int = Field(default=0, ge=0, description="Total favorite jobs saved")
    saved_searches: int = Field(default=0, ge=0, description="Total saved search queries")
    providers: int = Field(default=0, ge=0, description="Total active job providers")

    class Config:
        from_attributes = True
