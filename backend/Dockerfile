FROM python:3.12-slim

WORKDIR /app

# نسخ ملف الـ requirements أولاً للاستفادة من الـ Docker Cache
COPY requirements.txt .

# تثبيت المكتبات باستخدام pip المدمج في الصورة
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# فتح المنفذ 8000
EXPOSE 8000

# أمر تشغيل السيرفر مباشرة عبر uvicorn
CMD ["python", "-m", "uvicorn", "smarthunt.main:app", "--host", "0.0.0.0", "--port", "8000"]
