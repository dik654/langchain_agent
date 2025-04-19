from accelerate import Accelerator
from diffusers import DiffusionPipeline
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from PIL import Image
import base64
import io
import os
from datetime import datetime

# Accelerate 멀티 GPU 설정
accelerator = Accelerator()
print("🚀 SD3.5 Medium 모델 로딩 중...")

# 모델 로딩
pipe = DiffusionPipeline.from_pretrained(
    "/home/filadmin/ai/models/stable-diffusion-3.5-medium",
    torch_dtype=torch.float16,
    use_safetensors=True,
    local_files_only=True,
    variant="fp16"
)

# accelerate로 할당된 디바이스에 모델 올림
pipe.to(accelerator.device)

print("✅ 모델 준비 완료! Ready on", accelerator.device)

# FastAPI 서버 설정
app = FastAPI()

# 요청 포맷 정의
class PromptRequest(BaseModel):
    prompt: str

# 추론 엔드포인트
@app.post("/generate")
def generate_image(req: PromptRequest):
    with torch.autocast("cuda"):
        result = pipe(req.prompt).images[0]

    # 저장 경로 생성 (예: ./outputs)
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/{timestamp}.png"
    
    # 이미지 저장
    result.save(filename)

    return {
        "status": "ok",
        "prompt": req.prompt,
        "filename": filename,
    }
