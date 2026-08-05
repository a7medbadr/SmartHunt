from pydantic import BaseModel, ConfigDict, Field


class DashboardStatisticsResponse(BaseModel):
    jobs: int = Field(default=0, ge=0, description="Total number of available jobs")
    applications: int = Field(default=0, ge=0, description="Total job applications submitted")
    favorites: int = Field(default=0, ge=0, description="Total favorite jobs saved")
    linkedin_posts: int = Field(
        default=0, ge=0, description="Total jobs found via LinkedIn post scanning"
    )
    providers: int = Field(default=0, ge=0, description="Total active job providers")

    model_config = ConfigDict(from_attributes=True)
