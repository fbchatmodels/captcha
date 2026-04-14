import base64
import os
import re
import io
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Header, Request
import uvicorn
from PIL import Image
import pytesseract

app = FastAPI()

API_SECRET_KEY = "giaiautocaptchabydvfast"

def solve_universal_ocr(img_b64):
    try:
        # 1. Chuyển Base64 sang mảng OpenCV
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 2. Phóng to ảnh để xử lý nét hơn
        img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        # 3. Chuyển sang ảnh xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 4. Khử nhiễu (Dùng lọc nhiễu song phương để giữ lại cạnh chữ)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 5. Thuật toán tự động tách nền (Otsu's Thresholding)
        # Tự động tìm ngưỡng đen/trắng tối ưu cho từng ảnh khác nhau
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 6. Làm dầy nét chữ (Dilation) nếu chữ quá mảnh
        kernel = np.ones((2,2), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=1)

        # 7. Cấu hình Tesseract mạnh nhất
        # --psm 6: Coi là một khối chữ đồng nhất
        # Whitelist: Cho phép cả chữ hoa, chữ thường và số
        custom_config = r'--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        
        result = pytesseract.image_to_string(thresh, config=custom_config)
        
        # Làm sạch kết quả
        clean_text = re.sub(r'[^0-9a-zA-Z]', '', result).strip()
        return clean_text
    except Exception as e:
        print(f"Lỗi: {e}")
        return None

@app.post("/decrypt")
async def decrypt(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Key sai")
    data = await request.json()
    img_b64 = data.get("img_base64")
    result = solve_universal_ocr(img_b64)
    if result:
        return {"status": "success", "result": result}
    return {"status": "error", "message": "Không đọc được"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
