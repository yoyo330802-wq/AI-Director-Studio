# @title 📥 下载 Wan2.1 1.3B 模型
import os, subprocess

MODEL_DIR = "/workspace/ComfyUI/models/checkpoints"
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_FILE = "Wan2.1_T2V_1.3B_bf16.safetensors"
MODEL_PATH = f"{MODEL_DIR}/{MODEL_FILE}"

# 检查是否已存在
if os.path.exists(MODEL_PATH):
    print(f"✅ 模型已存在: {MODEL_FILE}")
    subprocess.run(["ls", "-lh", MODEL_PATH])
else:
    # 多个下载源
    URLs = [
        "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_T2V_1.3B_bf16.safetensors",
        "https://hf-mirror.com/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_T2V_1.3B_bf16.safetensors",
    ]
    
    for url in URLs:
        print(f"📥 尝试下载: {url.split('/')[-1]}")
        result = subprocess.run(
            ["wget", "-c", "-O", MODEL_PATH, url],
            capture_output=True, text=True
        )
        if result.returncode == 0 or os.path.exists(MODEL_PATH):
            print(f"✅ 下载完成!")
            subprocess.run(["ls", "-lh", MODEL_PATH])
            break
        else:
            print(f"⚠️  下载失败，尝试下一个源...")
    
    # 检查结果
    if os.path.exists(MODEL_PATH):
        size = os.path.getsize(MODEL_PATH) / (1024*1024*1024)
        print(f"📦 模型大小: {size:.2f} GB")
    else:
        print("❌ 所有下载源都失败了")
