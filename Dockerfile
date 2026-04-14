FROM python:3.9-slim

# Cài đặt hệ thống và thư viện cần thiết cho OpenCV/Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Chạy ứng dụng trên cổng của Render
CMD uvicorn tool:app --host 0.0.0.0 --port $PORT
