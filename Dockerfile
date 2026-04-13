# Sử dụng Python bản slim để tối ưu tốc độ build
FROM python:3.9-slim

# Cài đặt các thư viện hệ thống cần thiết cho OCR và xử lý ảnh
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào máy chủ
COPY . .

# Khởi động server (Render tự cấp cổng qua biến $PORT)
CMD uvicorn tool:app --host 0.0.0.0 --port $PORT
