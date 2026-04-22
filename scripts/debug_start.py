# @title 🐛 调试启动 (显示错误日志)
import os, subprocess, time, signal

WORKSPACE = "/workspace"

# 杀掉旧进程
subprocess.run(["pkill", "-9", "-f", "main.py"], capture_output=True)
time.sleep(3)

os.chdir(f"{WORKSPACE}/ComfyUI")
print("=" * 50)
print("🐛 启动 ComfyUI (显示日志)")
print("=" * 50)

# 启动并实时显示日志
proc = subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print("📜 日志输出:\n")

# 显示前100行日志
log_lines = []
for i, line in enumerate(proc.stdout):
    print(line.strip())
    log_lines.append(line.strip())
    if i > 100:
        break
    if "ERROR" in line.upper() or "error" in line.lower():
        print("^^^ 发现错误 ^^^")

# 等待一会儿再检查
print("\n⏳ 等待服务启动...")
time.sleep(30)

# 检查是否成功
try:
    import requests
    r = requests.get("http://localhost:8188/system_stats", timeout=5)
    if r.status_code == 200:
        print("\n🎉 启动成功!")
        stats = r.json()
        print(f"GPU: {stats['devices'][0]['name']}")
except Exception as e:
    print(f"\n❌ 启动失败: {e}")
    print("\n请检查上方日志中的错误信息")
