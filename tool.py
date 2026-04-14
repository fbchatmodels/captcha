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
        # Giải mã ảnh
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Phóng to ảnh cực đại (x5) để tách biệt các điểm nhiễu
        img = cv2.resize(img, None, fx=5, fy=5, interpolation=cv2.INTER_LANCZOS4)

        # 2. Chuyển sang ảnh xám và khử nhiễu đa tần
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. Kỹ thuật Adaptive Threshold kết hợp với Otsu để tạo độ tương phản tuyệt đối
        # Giúp loại bỏ nền màu và các đường kẻ mờ
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 21, 10)

        # 4. Max Level Processing: MORPH_OPEN & MORPH_CLOSE
        # MORPH_OPEN: Xóa các chấm nhiễu li ti và đường kẻ cực mảnh
        # MORPH_CLOSE: Lấp đầy các lỗ hổng bên trong chữ cái giúp chữ liền mạch
        kernel = np.ones((3,3), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

        # 5. Cấu hình Tesseract "Hardcore"
        # --oem 3: Dùng engine LSTM (Deep Learning) của Tesseract
        # --psm 6: Coi là một khối chữ đồng nhất
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
