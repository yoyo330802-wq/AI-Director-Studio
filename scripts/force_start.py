# @title 🔧 强制启动并显示日志
import os, subprocess, time

WORKSPACE = "/workspace"
os.chdir(WORKSPACE)

print("=" * 50)
print("🛠️  强制启动 ComfyUI")
print("=" * 50)

# 先杀掉可能存在的旧进程
subprocess.run(["pkill", "-9", "-f", "main.py"], capture_output=True)
time.sleep(2)

# 启动 ComfyUI (前台运行以查看日志)
os.chdir(f"{WORKSPACE}/ComfyUI")

print("🚀 启动中...\n")

# 启动并捕获输出
proc = subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# 等待启动并显示日志
started = False
for line in proc.stdout:
    print(line.strip())
    if "Starting server" in line or "Started server" in line or "Uvicorn running" in line:
        started = True
        break
    if "ERROR" in line or "error" in line.lower():
        print(f"⚠️  检测到错误: {line.strip()}")

if not started:
    print("\n⏳ 等待启动 (60秒)...")
    time.sleep(60)

print("\n" + "=" * 50)
print("✅ 尝试连接...")
print("=" * 50)

# 尝试连接
for i in range(15):
    try:
        import requests
        r = requests.get("http://localhost:8188/system_stats", timeout=3)
        if r.status_code == 200:
            print("🎉 成功连接!")
            stats = r.json()
            print(f"GPU: {stats['devices'][0]['name']}")
            models = requests.get("http://localhost:8188/api/models/checkpoints").json()
            print(f"模型: {models}")
            break
    except Exception as e:
        pass
    time.sleep(2)
    print(f"尝试 {i+1}/15...")
