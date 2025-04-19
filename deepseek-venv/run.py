import subprocess
import os

MODEL_PATH = "/home/filadmin/ai/models/DeepSeek-qwen-Bllossom-32B"

env = os.environ.copy()
env["CUDA_VISIBLE_DEVICES"] = "4,5,6,7"
env["NCCL_DEBUG"] = "INFO"
env["NCCL_P2P_DISABLE"] = "0"
#env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
#env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

subprocess.run(["python3", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", MODEL_PATH, \
     "--dtype", "float16", \
     "--tensor-parallel-size", "4", \
     "--max-num-seqs", "1", \
     "--max-model-len", "8192", \
     "--gpu-memory-utilization", "0.88", \
     "--host", "0.0.0.0", \
     "--enable-reasoning", \
     "--reasoning-parser", "deepseek_r1", \
     "--port", "8000"], env=env, stderr=subprocess.STDOUT)
