from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "UNIVA-Bllossom/DeepSeek-llama3.1-Bllossom-8B" # Replace with the ID of the model you want

# This line will download the model and tokenizer if not cached
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

print(f"Model '{model_id}' loaded successfully.")
# Now you can use the model and tokenizer

subprocess.run(["python3", "-m", "vllm.entrypoints.openai.api_server", \
             "--model", MODEL_PATH, \
                  "--dtype", "float16", \
                       "--tensor-parallel-size", "8", \
                            "--max-model-len", "8192", \
                                 "--gpu-memory-utilization", "0.85", \
                                      "--host", "0.0.0.0", \
                                           "--enable-reasoning", \
                                                "--reasoning-parser", "deepseek_r1", \
                                                     "--port", "8000"], env=env, stderr=subprocess.STDOUT)
