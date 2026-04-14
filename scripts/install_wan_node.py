# @title 🛠️ 安装 Wan2.1 自定义节点
import os, subprocess, time

WORKSPACE = "/workspace"
CUSTOM_NODES_DIR = f"{WORKSPACE}/ComfyUI/custom_nodes"

print("=" * 50)
print("🛠️ 安装 Wan2.1 节点")
print("=" * 50)

# 创建目录
os.makedirs(CUSTOM_NODES_DIR, exist_ok=True)
os.chdir(CUSTOM_NODES_DIR)

# 尝试安装 Wan2.1 节点
nodes = [
    ("https://github.com/kijai/ComfyUI-wan-video.git", "Wan video nodes"),
    ("https://github.com/AbigailXu/ComfyUI-Wan2.1.git", "Wan2.1 nodes"),
]

for repo, desc in nodes:
    node_name = repo.split("/")[-1].replace(".git", "")
    node_path = f"{CUSTOM_NODES_DIR}/{node_name}"
    
    if os.path.exists(node_path):
        print(f"✅ {desc} 已存在")
    else:
        print(f"📥 安装 {desc}...")
        result = subprocess.run(["git", "clone", repo], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {desc} 安装完成")
        else:
            print(f"⚠️  {desc} 安装失败")

# 检查已安装的节点
print("\n📁 已安装的自定义节点:")
for item in os.listdir(CUSTOM_NODES_DIR):
    if not item.startswith("_") and not item.startswith("."):
        print(f"  - {item}")

# 安装依赖
print("\n📦 安装节点依赖...")
subprocess.run(["pip", "install", "-r", "requirements.txt", "-q"], 
              cwd=f"{WORKSPACE}/ComfyUI", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("\n✅ 安装完成!")
print("请重启 ComfyUI (重新运行启动单元格)")
