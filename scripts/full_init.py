# @title 🏠 完整初始化 (克隆 + 下载模型 + 启动)
import os, subprocess, time

WORKSPACE = "/workspace"
os.makedirs(WORKSPACE, exist_ok=True)
os.chdir(WORKSPACE)

print("=" * 50)
print("🏠 完整初始化")
print("=" * 50)

# 1. 克隆 ComfyUI
if not os.path.exists(f"{WORKSPACE}/ComfyUI"):
    print("📦 克隆 ComfyUI...")
    subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git"], 
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ ComfyUI 克隆完成")
else:
    print("✅ ComfyUI 已存在")

# 2. 安装依赖
print("📦 安装依赖...")
subprocess.run(["pip", "install", "-r", "requirements.txt"], 
              cwd=f"{WORKSPACE}/ComfyUI", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("✅ 依赖安装完成")

# 3. 下载模型 (如果不存在)
MODEL_DIR = f"{WORKSPACE}/ComfyUI/models/checkpoints"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_FILE = "Wan2.1_T2V_1.3B_bf16.safetensors"
MODEL_PATH = f"{MODEL_DIR}/{MODEL_FILE}"

if os.path.exists(MODEL_PATH):
    print(f"✅ 模型已存在: {MODEL_FILE}")
else:
    print(f"📥 下载模型 {MODEL_FILE} (约2.6GB)...")
    urls = [
        "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_T2V_1.3B_bf16.safetensors",
    ]
    for url in urls:
        result = subprocess.run(["wget", "-c", "-O", MODEL_PATH, url], 
                              capture_output=True, text=True)
        if os.path.exists(MODEL_PATH):
            print(f"✅ 模型下载完成!")
            break
    else:
        print("⚠️  模型下载失败")

# 4. 启动 ComfyUI
print("\n🚀 启动 ComfyUI...")
os.chdir(f"{WORKSPACE}/ComfyUI")
subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    preexec_fn=os.setsid
)

print("⏳ 等待启动 (60秒)...")
time.sleep(60)

# 5. 检查状态
print("\n📊 检查状态...")
for i in range(10):
    try:
        import requests
        r = requests.get("http://localhost:8188/system_stats", timeout=3)
        if r.status_code == 200:
            stats = r.json()
            print(f"✅ GPU: {stats['devices'][0]['name']}")
            models = requests.get("http://localhost:8188/api/models/checkpoints").json()
            print(f"✅ 模型: {models}")
            break
    except:
        pass
    time.sleep(2)
    print(f"尝试 {i+1}/10...")

print("\n✅ 初始化完成!")
