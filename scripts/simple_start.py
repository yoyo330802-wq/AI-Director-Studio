# @title 🚀 简单启动
import os, subprocess, time

WORKSPACE = "/workspace"

# 1. 启动
os.chdir(f"{WORKSPACE}/ComfyUI")
subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
)

print("⏳ 启动中...")
time.sleep(45)

# 2. 检查
try:
    import requests
    r = requests.get("http://localhost:8188/system_stats", timeout=5)
    print("✅ 成功!")
    print(r.json()['devices'][0]['name'])
except Exception as e:
    print(f"❌ 失败: {e}")
