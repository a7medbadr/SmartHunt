FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium


COPY backend/ .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn","smarthunt.main:app","--host","0.0.0.0","--port","8000"]
