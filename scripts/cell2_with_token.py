# @title 🔗 获取访问链接
import subprocess, time
from IPython.display import display, HTML

!pip install pyngrok -q
from pyngrok import ngrok

# 填入ngrok token
NGROK_TOKEN = "3AtS4ViPYnX7CDmh4KYFlAmqmg2_sXhw7cUWmbDFC582iVDb"

if NGROK_TOKEN:
    ngrok.set_auth_token(NGROK_TOKEN)
    url = ngrok.connect(8188, "http")
    display(HTML(f"""
    <div style='padding:30px; background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:15px;margin:20px 0;'>
    <h2 style='color:#00ff88;margin:0;'>✅ ComfyUI 已就绪!</h2>
    <p style='margin:15px 0;'>🌐 访问地址:</p>
    <a href='{url}' target='_blank' style='font-size:28px;color:#00d4ff;text-decoration:none;word-break:break-all;'>{url}</a>
    <p style='color:#888;margin-top:20px;'>点击上方链接打开ComfyUI界面</p>
    </div>
    """))
else:
    print("🔗 使用localtunnel...")
    !npx localtunnel --port 8188
