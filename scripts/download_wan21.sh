#!/bin/bash
# =============================================================================
# Wan2.1 模型下载脚本
# 使用方法: bash download_wan21.sh
# =============================================================================

set -e

# 模型选择
MODEL_SIZE="${1:-1.3B}"  # 默认1.3B，可选14B

# 镜像源 (按优先级排序)
MIRRORS=(
    "https://hf-mirror.com"      # HuggingFace 镜像
    "https://huggingface.co"      # 原始源
)

# 下载目录
DOWNLOAD_DIR="/workspace/ComfyUI/models/checkpoints"
mkdir -p "$DOWNLOAD_DIR"

echo "========================================"
echo "  Wan2.1 模型下载器"
echo "========================================"
echo "模型: $MODEL_SIZE"
echo "目录: $DOWNLOAD_DIR"
echo ""

# 模型信息
case $MODEL_SIZE in
    "1.3B")
        MODEL_FILE="Wan2.1_T2V_1.3B_bf16.safetensors"
        FILE_SIZE="约 2.6GB"
        ;;
    "14B")
        MODEL_FILE="Wan2.1_T2V_14B_bf16.safetensors"
        FILE_SIZE="约 28GB"
        ;;
    *)
        echo "错误: 不支持的模型 $MODEL_SIZE"
        echo "支持: 1.3B, 14B"
        exit 1
        ;;
esac

TARGET_FILE="$DOWNLOAD_DIR/$MODEL_FILE"

# 检查是否已存在
if [ -f "$TARGET_FILE" ]; then
    echo "✅ 模型已存在: $MODEL_FILE"
    ls -lh "$TARGET_FILE"
    exit 0
fi

# 尝试下载
download_model() {
    local mirror=$1
    local url="$mirror/Wan-AI/Wan2.1-T2V-${MODEL_SIZE}/resolve/main/$MODEL_FILE"
    
    echo "尝试: $url"
    
    if curl -sI "$url" > /dev/null 2>&1; then
        echo "✅ 下载中 (可能需要几分钟)..."
        curl -L -o "$TARGET_FILE" "$url" --progress-bar
        return 0
    fi
    return 1
}

# 尝试各个镜像
for mirror in "${MIRRORS[@]}"; do
    echo "📥 从 $mirror 下载..."
    if download_model "$mirror"; then
        echo ""
        echo "✅ 下载完成!"
        ls -lh "$TARGET_FILE"
        exit 0
    fi
done

echo ""
echo "⚠️  自动下载失败，请手动下载:"
echo ""
echo "1. 访问: https://huggingface.co/Wan-AI/Wan2.1-T2V-${MODEL_SIZE}"
echo "2. 下载: $MODEL_FILE"
echo "3. 保存到: $DOWNLOAD_DIR/"
echo ""
echo "或使用其他下载方式:"
echo "  - 通过浏览器下载后上传"
echo "  - 使用 wget/curl 直接下载"
