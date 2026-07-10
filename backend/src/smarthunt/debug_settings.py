from smarthunt.core.config import get_settings

settings = get_settings()

print(settings.model_dump())
