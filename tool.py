import base64
import cv2
import numpy as np
import io
import re
import os
from fastapi import FastAPI, Header, Request, HTTPException
import uvicorn
import pytesseract

app = FastAPI()
API_SECRET_KEY = "giaiautocaptchabydvfast"

def solve_max_level_ocr(img_b64):
    try:
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Phóng to ảnh (x4) - Bước này bắt buộc để AI nhìn rõ nét chữ
        img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)

        # 2. Chuyển sang ảnh xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Khử nhiễu trắng (Dùng Median Blur để xóa các hạt li ti)
        gray = cv2.medianBlur(gray, 3)

        # 4. Ngưỡng thích nghi (Tạo ảnh trắng đen cực nét)
        # Chỉnh hằng số C = 10 để xóa bớt các đường gạch mờ
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 21, 10)

        # 5. CHIÊU QUYẾT ĐỊNH: Xói mòn (Erosion) rồi lại Giãn nở (Dilation)
        # Đường kẻ thường mảnh hơn nét chữ -> Xói mòn sẽ làm biến mất đường kẻ
        # Sau đó Giãn nở lại để chữ lấy lại vóc dáng cũ
        kernel = np.ones((2,2), np.uint8)
        processed = cv2.erode(thresh, kernel, iterations=1) # Bào mòn đường kẻ
        processed = cv2.dilate(processed, kernel, iterations=1) # Đắp lại nét chữ

        # 6. Đọc chữ (Ưu tiên engine LSTM mới nhất)
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        result = pytesseract.image_to_string(processed, config=custom_config)

        clean_text = re.sub(r'[^0-9A-Z]', '', result).strip()
        return clean_text
    except Exception as e:
        return None

@app.post("/decrypt")
async def decrypt(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403)
    data = await request.json()
    res = solve_max_level_ocr(data.get("img_base64"))
    return {"status": "success", "result": res} if res else {"status": "error", "message": "AI Blind"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
