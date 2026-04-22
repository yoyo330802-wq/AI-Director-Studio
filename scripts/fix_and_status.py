# @title 🔧 修复启动 + 查看状态
import os, subprocess, time, threading

WORKSPACE = "/workspace"
os.chdir(WORKSPACE)

print("=" * 50)
print("🔧 检查 ComfyUI 状态")
print("=" * 50)

# 检查 ComfyUI 是否在运行
result = subprocess.run(["pgrep", "-f", "main.py"], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ ComfyUI 进程正在运行")
    pid = result.stdout.strip().split('\n')[0]
    print(f"   PID: {pid}")
else:
    print("❌ ComfyUI 未运行，准备启动...")
    
    # 启动 ComfyUI
    os.chdir(f"{WORKSPACE}/ComfyUI")
    subprocess.Popen(
        ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    print("⏳ 等待启动 (30秒)...")
    time.sleep(30)
    print("✅ 已启动")

# 等待服务就绪
print("\n⏳ 等待服务就绪...")
for i in range(10):
    try:
        import requests
        r = requests.get("http://localhost:8188/system_stats", timeout=3)
        if r.status_code == 200:
            print("✅ 服务已就绪!")
            break
    except:
        pass
    time.sleep(2)
    print(f"   尝试 {i+1}/10...")

# 显示状态
try:
    import requests
    stats = requests.get("http://localhost:8188/system_stats").json()
    print("\n" + "=" * 50)
    print("📊 系统状态")
    print("=" * 50)
    print(f"GPU: {stats['devices'][0]['name']}")
    print(f"显存: {stats['devices'][0]['vram_free']/1024**3:.1f}GB 可用")
    
    models = requests.get("http://localhost:8188/api/models/checkpoints").json()
    print(f"\n📦 模型: {len(models)} 个")
    for m in models:
        print(f"   - {m}")
except Exception as e:
    print(f"❌ 获取状态失败: {e}")
