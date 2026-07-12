# Hugging Face Spaces (Docker SDK) serves on port 7860.
FROM python:3.12-slim
WORKDIR /app
# tesseract-ocr: local-OCR fallback for /api/resume-image when GEMINI_API_KEY
# isn't configured/working (see main.py's local_ocr_text()) -- keeps that
# endpoint functional at $0 with no external key dependency.
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
