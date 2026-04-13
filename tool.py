import base64
import os
import re
import io
from fastapi import FastAPI, HTTPException, Header, Request
import uvicorn
from PIL import Image
import pytesseract

app = FastAPI()

# Key bảo mật của Minh Vũ
API_SECRET_KEY = "giaiautocaptchabydvfast"

def solve_image_captcha(img_b64):
    try:
        # Giải mã Base64 sang Byte ảnh
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes))
        
        # --- TIỀN XỬ LÝ ẢNH (GIÚP AI SÁNG MẮT) ---
        img = img.convert('L')  # Chuyển sang ảnh xám
        # Lọc nhiễu: Điểm nào tối cho thành đen (0), sáng cho thành trắng (255)
        img = img.point(lambda x: 0 if x < 140 else 255, '1') 
        
        # Sử dụng Tesseract để đọc chữ/số
        # config='--psm 7' dùng để đọc 1 dòng chữ duy nhất
        result = pytesseract.image_to_string(img, config='--psm 7')
        
        # Chỉ lấy chữ cái và số, xóa bỏ ký tự lạ
        clean_text = re.sub(r'[^0-9a-zA-Z]', '', result).strip()
        return clean_text
    except Exception as e:
        print(f"Lỗi xử lý OCR: {e}")
        return None

@app.get("/")
async def root():
    return {"status": "active", "owner": "Minh Vu", "engine": "Tesseract OCR"}

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
    # Chạy trên Port của Render
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
