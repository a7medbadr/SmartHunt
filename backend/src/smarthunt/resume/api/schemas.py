from pydantic import BaseModel


class ResumeProfileRequest(BaseModel):
    resume: str


class ResumeProfileResponse(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    current_title: str | None = None
    current_company: str | None = None

    years_of_experience: float | None = None

    country: str | None = None
    city: str | None = None
    nationality: str | None = None

    education: str | None = None

    skills: list[str] = []
    languages: list[str] = []
    certifications: list[str] = []
    projects: list[str] = []

    salary_expectation: str | None = None
    notice_period: str | None = None
    summary: str | None = None
