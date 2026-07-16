from uuid import uuid4
from datetime import datetime

class ResumePersistenceService:

    async def save(self, filename: str, text: str):

        return {
            "id": str(uuid4()),
            "filename": filename,
            "characters": len(text),
            "created_at": datetime.utcnow().isoformat()
        }

service = ResumePersistenceService()
