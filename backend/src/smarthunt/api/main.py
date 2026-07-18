from fastapi import FastAPI

from smarthunt.cover_letter import cover_letter_router
from smarthunt.recruitment import recruitment_router

app = FastAPI(title="SmartHunt API")

# Register Routers
app.include_router(cover_letter_router)
app.include_router(recruitment_router)
