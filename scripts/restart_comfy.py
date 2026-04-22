# @title 🔄 重启 ComfyUI
import os, subprocess, time

WORKSPACE = "/workspace"

# 杀掉旧进程
subprocess.run(["pkill", "-9", "-f", "main.py"], capture_output=True)
time.sleep(3)

# 重新启动
os.chdir(f"{WORKSPACE}/ComfyUI")
subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
)

print("⏳ 等待启动 (60秒)...")
time.sleep(60)

# 检查
try:
    import requests
    r = requests.get("http://localhost:8188/system_stats", timeout=5)
    print("✅ 启动成功!")
    print(f"GPU: {r.json()['devices'][0]['name']}")
except Exception as e:
    print(f"❌ {e}")
