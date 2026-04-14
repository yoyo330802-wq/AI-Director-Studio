# @title 🌐 获取访问链接
!pip install pyngrok -q
from pyngrok import ngrok

ngrok.set_auth_token("3AtS4ViPYnX7CDmh4KYFlAmqmg2_sXhw7cUWmbDFC582iVDb")
url = ngrok.connect(8188, "http")

print("=" * 50)
print("🌐 访问链接:")
print("=" * 50)
print(url)
print("=" * 50)
print("点击上方链接访问 ComfyUI")
