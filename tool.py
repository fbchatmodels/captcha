import base64
import os
import re
import io
from fastapi import FastAPI, HTTPException, Header, Request
import uvicorn
from PIL import Image
import pytesseract

app = FastAPI()

# Key bảo mật để không cho người lạ dùng chùa API của bạn
API_SECRET_KEY = "giaiautocaptchabydvfast"

def solve_image_captcha(img_b64):
    try:
        # Giải mã ảnh từ PHP gửi lên
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Xử lý ảnh sang đen trắng để đọc chuẩn hơn
        img = img.convert('L') 
        
        # OCR nhận diện chữ số
        result = pytesseract.image_to_string(img, config='--psm 7')
        return re.sub(r'[^0-9a-zA-Z]', '', result).strip()
    except Exception as e:
        print(f"Lỗi OCR: {e}")
        return None

@app.get("/")
async def root():
    return {"status": "running", "message": "API Captcha của Minh Vũ đang hoạt động"}

@app.post("/decrypt")
async def decrypt_captcha(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Sai Key bảo mật!")

    try:
        data = await request.json()
        img_b64 = data.get("img_base64")
        
        if not img_b64:
            return {"status": "error", "message": "Thiếu dữ liệu ảnh (base64)"}

        result = solve_image_captcha(img_b64)
        
        if result:
            return {"status": "success", "result": result}
        else:
            return {"status": "error", "message": "Không thể đọc được ảnh"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Render yêu cầu chạy trên port do họ cấp qua biến môi trường
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
