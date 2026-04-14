# @title 🔄 重新初始化 + 启动
import os, subprocess, time

WORKSPACE = "/workspace"
os.makedirs(WORKSPACE, exist_ok=True)
os.chdir(WORKSPACE)

print("=" * 50)
print("🔄 重新初始化")
print("=" * 50)

# 1. 克隆 ComfyUI
if not os.path.exists(f"{WORKSPACE}/ComfyUI"):
    print("📦 克隆 ComfyUI (约1分钟)...")
    subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git"], 
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ 克隆完成")
else:
    print("✅ ComfyUI 已存在")

# 2. 安装依赖
print("📦 安装依赖...")
subprocess.run(["pip", "install", "-r", "requirements.txt", "-q"], 
              cwd=f"{WORKSPACE}/ComfyUI", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("✅ 依赖完成")

# 3. 检查模型
MODEL_PATH = f"{WORKSPACE}/ComfyUI/models/checkpoints/Wan2.1_T2V_1.3B_bf16.safetensors"
if os.path.exists(MODEL_PATH):
    print("✅ 模型已存在")
else:
    print("⚠️  模型不存在，需要重新下载")

# 4. 启动
print("\n🚀 启动 ComfyUI...")
os.chdir(f"{WORKSPACE}/ComfyUI")
subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
)

print("⏳ 等待启动 (60秒)...")
time.sleep(60)

# 5. 检查
try:
    import requests
    r = requests.get("http://localhost:8188/system_stats", timeout=5)
    print("✅ 启动成功!")
    print(f"GPU: {r.json()['devices'][0]['name']}")
except Exception as e:
    print(f"❌ 失败: {e}")
