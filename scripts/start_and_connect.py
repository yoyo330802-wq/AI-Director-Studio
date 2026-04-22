# @title 🚀 启动 ComfyUI + 获取访问链接
import os, subprocess, time, threading
from IPython.display import display, HTML

WORKSPACE = "/workspace"

# 1. 启动 ComfyUI (如果没运行的话)
def start_comfyui():
    os.chdir(f"{WORKSPACE}/ComfyUI")
    subprocess.Popen(
        ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

# 检查是否已运行
try:
    import requests
    r = requests.get("http://localhost:8188/system_stats", timeout=2)
    print("✅ ComfyUI 已在运行")
except:
    print("⏳ 启动 ComfyUI 中...")
    threading.Thread(target=start_comfyui).start()
    time.sleep(20)
    print("✅ ComfyUI 已启动")

# 2. 获取 ngrok 链接
!pip install pyngrok -q
from pyngrok import ngrok

NGROK_TOKEN = "3AtS4ViPYnX7CDmh4KYFlAmqmg2_sXhw7cUWmbDFC582iVDb"
ngrok.set_auth_token(NGROK_TOKEN)

url = ngrok.connect(8188, "http")
display(HTML(f"""
<div style='padding:25px; background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:15px;margin:15px 0;'>
<h2 style='color:#00ff88;'>✅ ComfyUI 已就绪!</h2>
<p>🌐 访问地址:</p>
<a href='{url}' target='_blank' style='font-size:24px;color:#00d4ff;'>{url}</a>
</div>
"""))

# 显示模型状态
import requests
models = requests.get("http://localhost:8188/api/models/checkpoints").json()
print(f"📦 模型数量: {len(models)}")
for m in models:
    print(f"  - {m}")
