FROM python:3.12-slim

WORKDIR /app

# نسخ ملف الاعتماديات أولاً لاستغلال الـ Cache
COPY requirements.txt .

# تثبيت المكتبات الخارجية
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات المشروع بالكامل
COPY . .

# حل مشكلة hatchling: إنشاء ملف README.md في المجلد الأب لكي يجده محرك البناء
RUN touch ../README.md

# تثبيت مشروعك محلياً بدون تحميل أي اعتماديات مجدداً
RUN pip install --no-deps .

EXPOSE 8000

# تشغيل uvicorn بشكل مباشر
CMD ["uvicorn", "smarthunt.main:app", "--host", "0.0.0.0", "--port", "8000"]


HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD curl -fsS http://localhost:8000/api/v1/health/live || exit 1
