from fastapi import FastAPI
from pydantic import BaseModel
from diffusers import StableDiffusionXLPipeline
import torch
from PIL import Image
import io
import base64
import os

# 오프라인 실행 설정
os.environ["CUDA_VISIBLE_DEVICES"] = "2,3"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# FastAPI 인스턴스
app = FastAPI()

# 요청 모델
class PromptRequest(BaseModel):
    prompt: str

# 모델 경로
MODEL_PATH = "/home/filadmin/ai/models/stable-diffusion-3.5-large"

# ✅ 모델 로딩
print("🚀 Stable Diffusion 로딩 중...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    use_safetensors=True,
    local_files_only=True
)

# ✅ U-Net을 2GPU에 분산
if torch.cuda.device_count() < 2:
    raise RuntimeError("⚠️ 최소 2개의 GPU가 필요합니다.")

pipe.unet = torch.nn.DataParallel(pipe.unet, device_ids=[0, 1])
pipe.to("cuda")

# ✅ Warmup (최초 추론 시간 단축)
_ = pipe("warmup test").images[0]
print("✅ 모델 준비 완료!")

# ✅ POST /generate
@app.post("/generate")
def generate(req: PromptRequest):
    try:
        image = pipe(req.prompt).images[0]
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "status": "ok",
            "prompt": req.prompt,
            "image_base64": img_base64
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

