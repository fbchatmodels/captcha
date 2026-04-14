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

def solve_ultra_final_ocr(img_b64):
    try:
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Phóng to ảnh x3 (vừa đủ để không làm vỡ nét)
        img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        # 2. Chuyển sang ảnh xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Kỹ thuật xóa đường kẻ: Dùng Threshold nhị phân ngược
        # Những gì không phải chữ sẽ bị ép về trắng
        _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)

        # 4. Lọc bỏ các nét mảnh (Noise Removal)
        # Dùng kernel 3x1 và 1x3 để triệt tiêu các đường kẻ ngang/dọc mảnh
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
        
        # Xử lý hình thái học để làm sạch nền
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_h, iterations=1)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel_v, iterations=1)

        # 5. Làm dầy lại nét chữ sau khi lọc
        kernel_bold = np.ones((2,2), np.uint8)
        processed = cv2.dilate(processed, kernel_bold, iterations=1)

        # 6. Nhận diện (PSM 7 là tốt nhất cho 1 dòng captcha)
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        result = pytesseract.image_to_string(processed, config=custom_config)

        clean_text = re.sub(r'[^0-9A-Z]', '', result).strip()
        # Nếu giải ra quá ngắn hoặc quá dài (hệ thống thường là 4-6 ký tự), trả về None để retry
        if len(clean_text) < 3 or len(clean_text) > 8:
            return None
        return clean_text
    except:
        return None

@app.post("/decrypt")
async def decrypt(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403)
    try:
        data = await request.json()
        res = solve_ultra_final_ocr(data.get("img_base64"))
        if res:
            return {"status": "success", "result": res}
        return {"status": "error", "message": "AI Blind"}
    except:
        return {"status": "error", "message": "Crash"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
