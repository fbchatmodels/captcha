import base64
import cv2
import numpy as np
import io
import re
import os
from fastapi import FastAPI, Header, Request, HTTPException
import uvicorn
import pytesseract
from PIL import Image

app = FastAPI()

# Key bảo mật của Minh Vũ
API_SECRET_KEY = "giaiautocaptchabydvfast"

def solve_universal_captcha(img_b64):
    try:
        # Giải mã base64
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # BƯỚC 1: Phóng to ảnh x4 để tách các đường kẻ nhiễu mảnh
        img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)

        # BƯỚC 2: Chuyển sang ảnh xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # BƯỚC 3: Lọc nhiễu Median (Xóa các hạt bụi và đường kẻ li ti)
        gray = cv2.medianBlur(gray, 3)

        # BƯỚC 4: Ngưỡng thích nghi (Adaptive Threshold)
        # Tự động tách chữ ra khỏi nền dù nền có nhiều màu hay ánh sáng không đều
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)

        # BƯỚC 5: Tẩy đốm nhiễu còn sót lại (Morphology)
        kernel = np.ones((2,2), np.uint8)
        processed_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # BƯỚC 6: Nhận diện bằng Tesseract
        # --psm 6: Coi ảnh là một khối văn bản (linh hoạt số lượng ký tự)
        custom_config = r'--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        result = pytesseract.image_to_string(processed_img, config=custom_config)

        # Làm sạch kết quả: chỉ lấy chữ và số
        return re.sub(r'[^0-9a-zA-Z]', '', result).strip()
    except Exception as e:
        print(f"Lỗi xử lý: {e}")
        return None

@app.get("/")
async def root():
    return {"status": "running", "mode": "universal_ocr"}

@app.post("/decrypt")
async def decrypt(request: Request, x_api_key: str = Header(None)):
    # Kiểm tra Key bảo mật
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        data = await request.json()
        img_b64 = data.get("img_base64")
        
        if not img_b64:
            return {"status": "error", "message": "No data"}
            
        captcha_text = solve_universal_captcha(img_b64)
        
        if captcha_text:
            return {"status": "success", "result": captcha_text}
        else:
            return {"status": "error", "message": "Could not read captcha"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
