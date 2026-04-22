# @title 🐛 查看启动日志
import os, subprocess, time

WORKSPACE = "/workspace"

# 杀掉旧进程
subprocess.run(["pkill", "-9", "-f", "main.py"], capture_output=True)
time.sleep(2)

os.chdir(f"{WORKSPACE}/ComfyUI")

print("🚀 启动中...\n")

# 启动并显示日志
proc = subprocess.Popen(
    ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# 显示前80行日志
for i, line in enumerate(proc.stdout):
    print(line.strip())
    if i > 80:
        break
    if "ERROR" in line.upper():
        print("^^^^^^^ 错误 ^^^^^^^")
