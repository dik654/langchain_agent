import subprocess
import os

MODEL_PATH = "/home/filadmin/ai/models/DeepSeek-qwen-Bllossom-32B"

env = os.environ.copy()
env["CUDA_VISIBLE_DEVICES"] = "0,1,2,3,4,5,6,7"
env["NCCL_DEBUG"] = "INFO"
env["NCCL_P2P_DISABLE"] = "0"
env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

subprocess.run(["python3", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", MODEL_PATH, \
     "--dtype", "float16", \
     "--tensor-parallel-size", "8", \
     "--max-model-len", "8192", \
     "--gpu-memory-utilization", "0.80", \
     "--enable-reasoning", \
     "--reasoning-parser", "deepseek_r1", \
     "--host", "0.0.0.0", \
     "--port", "8000"], env=env, stderr=subprocess.STDOUT)
