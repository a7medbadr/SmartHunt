import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class DashboardTimeseriesPoint(BaseModel):
    date: dt.date = Field(description="Calendar day (UTC) this point covers")
    job_sites: int = Field(default=0, ge=0, description="Jobs discovered from job sites that day")
    linkedin_posts: int = Field(
        default=0, ge=0, description="Jobs discovered from LinkedIn posts that day"
    )
    whatsapp_posts: int = Field(
        default=0, ge=0, description="Jobs discovered from WhatsApp messages that day"
    )
    applications: int = Field(default=0, ge=0, description="Applications submitted that day")

    model_config = ConfigDict(from_attributes=True)


class DashboardTimeseriesResponse(BaseModel):
    points: list[DashboardTimeseriesPoint] = Field(
        default_factory=list,
        description="One point per calendar day, oldest first, zero-filled for days with no activity",
    )


class DashboardStatisticsResponse(BaseModel):
    jobs: int = Field(default=0, ge=0, description="Total number of available jobs")
    applications: int = Field(default=0, ge=0, description="Total job applications submitted")
    favorites: int = Field(default=0, ge=0, description="Total favorite jobs saved")
    linkedin_posts: int = Field(
        default=0,
        ge=0,
        description="Jobs found via LinkedIn post scanning still pending review (matches the /jobs/linkedin tab)",
    )
    whatsapp_posts: int = Field(
        default=0,
        ge=0,
        description="Jobs found via WhatsApp channel/group scanning still pending review (matches the /jobs/whatsapp tab)",
    )
    job_sites: int = Field(
        default=0,
        ge=0,
        description="Jobs found via real job-site discovery still pending review (matches the /jobs/sites tab)",
    )
    not_suitable_jobs: int = Field(
        default=0, ge=0, description="Total jobs the owner has marked not suitable"
    )
    providers: int = Field(default=0, ge=0, description="Total active job providers")

    model_config = ConfigDict(from_attributes=True)
