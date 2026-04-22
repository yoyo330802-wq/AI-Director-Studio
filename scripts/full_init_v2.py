# @title 🚀 完整初始化 (克隆+依赖+模型+启动)
import os, subprocess, time

WORKSPACE = "/workspace"
os.makedirs(WORKSPACE, exist_ok=True)
os.chdir(WORKSPACE)

print("=" * 50)
print("🚀 完整初始化")
print("=" * 50)

# 1. 克隆
if not os.path.exists(f"{WORKSPACE}/ComfyUI"):
    print("📦 克隆 ComfyUI...")
    subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git"], 
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ 完成")

# 2. 依赖
print("📦 安装依赖...")
subprocess.run(["pip", "install", "-r", "requirements.txt", "-q"], 
              cwd=f"{WORKSPACE}/ComfyUI", stdout=subprocess.DEVNULL)
print("✅ 完成")

# 3. 模型
MODEL_DIR = f"{WORKSPACE}/ComfyUI/models/checkpoints"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_FILE = "Wan2.1_T2V_1.3B_bf16.safetensors"
MODEL_PATH = f"{MODEL_DIR}/{MODEL_FILE}"

if os.path.exists(MODEL_PATH):
    size = os.path.getsize(MODEL_PATH) / (1024**3)
    if size > 1:
        print(f"✅ 模型已存在 ({size:.1f}GB)")
    else:
        print(f"⚠️  模型文件异常 ({size:.1f}GB)，重新下载...")
        os.remove(MODEL_PATH)
        subprocess.run(["rm", "-f", MODEL_PATH])

if not os.path.exists(MODEL_PATH):
    print("📥 下载模型 (约2.6GB)...")
    url = "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_T2V_1.3B_bf16.safetensors"
    result = subprocess.run(
        ["wget", "-c", "-O", MODEL_PATH, url],
        capture_output=True, text=True
    )
    if os.path.exists(MODEL_PATH):
        size = os.path.getsize(MODEL_PATH) / (1024**3)
        print(f"✅ 模型完成 ({size:.1f}GB)")
    else:
        print("❌ 模型下载失败")

# 4. 启动
print("\n🚀 启动 ComfyUI...")
os.chdir(f"{WORKSPACE}/ComfyUI")
subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
)

print("⏳ 等待启动 (90秒)...")
time.sleep(90)

# 5. 检查
print("\n📊 检查状态...")
try:
    import requests
    r = requests.get("http://localhost:8188/system_stats", timeout=5)
    stats = r.json()
    print(f"✅ GPU: {stats['devices'][0]['name']}")
    vram = stats['devices'][0]['vram_free'] / 1024**3
    print(f"✅ 显存: {vram:.1f}GB 可用")
    
    models = requests.get("http://localhost:8188/api/models/checkpoints").json()
    print(f"✅ 模型: {models}")
except Exception as e:
    print(f"❌ {e}")
