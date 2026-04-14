import base64
import os
import re
import io
from fastapi import FastAPI, HTTPException, Header, Request
import uvicorn
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract

app = FastAPI()

# Key bảo mật của Minh Vũ
API_SECRET_KEY = "giaiautocaptchabydvfast"

def solve_image_captcha(img_b64):
    try:
        # 1. Giải mã Base64 sang Byte ảnh
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # 2. Phóng to ảnh (Rất quan trọng cho Tesseract)
        # Phóng to giúp các nét chữ tách rời khỏi các đường kẻ nhiễu mảnh
        w, h = img.size
        img = img.resize((w * 3, h * 3), Image.Resampling.LANCZOS)
        
        # 3. Tăng độ tương phản và độ nét
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0) # Tăng tương phản lên gấp đôi
        img = img.filter(ImageFilter.SHARPEN) # Làm sắc nét cạnh chữ
        
        # 4. Chuyển sang ảnh xám
        img = img.convert('L')
        
        # 5. Khử nhiễu bằng Threshold (Ngưỡng)
        # Chuyển về hệ nhị phân (chỉ đen và trắng)
        # Các pixel mờ (đường kẻ nhiễu) sẽ bị biến thành trắng (255)
        # Các pixel đậm (chữ) sẽ biến thành đen (0)
        img = img.point(lambda x: 0 if x < 135 else 255, '1')
        
        # 6. Cấu hình Tesseract tối ưu cho Captcha
        # --psm 7: Coi là 1 dòng chữ duy nhất
        # tessedit_char_whitelist: Chỉ cho phép đọc các ký tự có trong Captcha để tránh ra ký tự lạ
        custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        
        result = pytesseract.image_to_string(img, config=custom_config)
        
        # Làm sạch kết quả
        clean_text = re.sub(r'[^0-9a-zA-Z]', '', result).strip()
        
        # Debug nhẹ: Nếu kết quả rỗng, thử psm 8 (coi là 1 từ duy nhất)
        if not clean_text:
            result = pytesseract.image_to_string(img, config=r'--psm 8')
            clean_text = re.sub(r'[^0-9a-zA-Z]', '', result).strip()

        return clean_text
    except Exception as e:
        print(f"Lỗi xử lý OCR: {e}")
        return None

@app.get("/")
async def root():
    return {"status": "active", "owner": "Minh Vu", "version": "2.0-Optimized"}

@app.post("/decrypt")
async def decrypt_captcha(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Key bảo mật không chính xác")

    try:
        data = await request.json()
        img_b64 = data.get("img_base64")
        
        if not img_b64:
            return {"status": "error", "message": "Thiếu dữ liệu img_base64"}

        result = solve_image_captcha(img_b64)
        
        if result:
            return {"status": "success", "result": result}
        else:
            return {"status": "error", "message": "AI không nhìn rõ ảnh"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
