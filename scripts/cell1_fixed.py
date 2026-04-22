# @title ▶️ Wan2.1 ComfyUI 启动器 (修复版)
import os, subprocess, time
from IPython.display import display, HTML

WORKSPACE = "/workspace"
os.makedirs(WORKSPACE, exist_ok=True)
os.chdir(WORKSPACE)

# 检查GPU (修复版本)
try:
    result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader"], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print("🖥️  GPU状态:")
        print(result.stdout)
    else:
        print("⚠️  未检测到GPU，请确认运行时设置")
except Exception as e:
    print("⚠️  GPU检测失败:", str(e))
    print("请确认: Runtime → Change runtime type → L4 GPU")

# 克隆ComfyUI
if not os.path.exists(f"{WORKSPACE}/ComfyUI"):
    print("📦 克隆ComfyUI中...")
    subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git"], 
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pip", "install", "-r", "requirements.txt"], 
                  cwd=f"{WORKSPACE}/ComfyUI", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ ComfyUI安装完成")
else:
    print("✅ ComfyUI已存在")

# 启动ComfyUI
import threading
def start():
    os.chdir(f"{WORKSPACE}/ComfyUI")
    subprocess.Popen(
        ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"], 
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
        preexec_fn=os.setsid
    )

threading.Thread(target=start).start()
print("⏳ ComfyUI启动中(约30秒)...")
time.sleep(30)
print("✅ ComfyUI已启动!")
