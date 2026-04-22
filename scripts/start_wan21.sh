#!/bin/bash
# =============================================================================
# 漫AI - Wan2.1 本地启动脚本
# 适用于自有GPU集群 (如 4×H100)
# =============================================================================

set -e

# 配置
COMFYUI_DIR="${COMFYUI_DIR:-/opt/ComfyUI}"
MODEL_SIZE="${MODEL_SIZE:-14B}"  # 1.3B, 14B, 2.2
PORT="${PORT:-8188}"
NGINX_PORT="${NGINX_PORT:-80}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查GPU
check_gpu() {
    log_info "检查GPU..."
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    log_success "检测到 $GPU_COUNT 张GPU"
}

# 安装依赖
install_deps() {
    log_info "安装系统依赖..."
    apt-get update
    apt-get install -y git-lfs wget curl
    
    log_info "克隆 ComfyUI..."
    if [ ! -d "$COMFYUI_DIR" ]; then
        git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
    fi
    
    log_info "安装Python依赖..."
    cd "$COMFYUI_DIR"
    pip install -r requirements.txt
    pip install xformers
    
    log_success "依赖安装完成"
}

# 下载模型
download_model() {
    log_info "下载 Wan2.1 $MODEL_SIZE 模型..."
    
    MODEL_DIR="$COMFYUI_DIR/models/checkpoints"
    mkdir -p "$MODEL_DIR"
    
    case $MODEL_SIZE in
        "1.3B")
            MODEL_FILE="Wan2.1_T2V_1.3B_bf16.safetensors"
            MODEL_URL="https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/$MODEL_FILE"
            ;;
        "14B")
            MODEL_FILE="Wan2.1_T2V_14B_bf16.safetensors"
            MODEL_URL="https://huggingface.co/Wan-AI/Wan2.1-T2V-14B/resolve/main/$MODEL_FILE"
            ;;
        "2.2")
            MODEL_FILE="Wan2.2_T2V.safetensors"
            MODEL_URL="https://huggingface.co/Wan-AI/Wan2.2-T2V/resolve/main/$MODEL_FILE"
            ;;
    esac
    
    if [ -f "$MODEL_DIR/$MODEL_FILE" ]; then
        log_warn "模型已存在: $MODEL_FILE"
    else
        cd "$MODEL_DIR"
        wget -c "$MODEL_URL" -O "$MODEL_FILE"
    fi
    
    log_success "模型准备完成"
}

# 启动 ComfyUI
start_comfyui() {
    log_info "启动 ComfyUI (Wan2.1 $MODEL_SIZE)..."
    
    cd "$COMFYUI_DIR"
    
    # 使用 GPU 加速
    export CUDA_VISIBLE_DEVICES=0,1,2,3  # 使用全部4张H100
    
    # 启动
    python3 main.py \
        --listen 0.0.0.0 \
        --port $PORT \
        --preview-method auto \
        &
    
    log_success "ComfyUI 已启动: http://localhost:$PORT"
}

# 启动 Web UI (可选)
start_webui() {
    log_info "检查自定义节点..."
    
    # 安装 Wan2.1 自定义节点
    CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
    mkdir -p "$CUSTOM_NODES_DIR"
    
    if [ ! -d "$CUSTOM_NODES_DIR/ComfyUI-Wan2.1" ]; then
        cd "$CUSTOM_NODES_DIR"
        git clone https://github.com/AbigailXu/ComfyUI-Wan2.1.git
    fi
    
    log_success "自定义节点安装完成"
}

# 显示状态
show_status() {
    echo ""
    echo "=========================================="
    echo "  漫AI - Wan2.1 服务状态"
    echo "=========================================="
    echo ""
    echo "  ComfyUI: http://localhost:$PORT"
    echo "  模型: Wan2.1 $MODEL_SIZE"
    echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    echo ""
    echo "  常用命令:"
    echo "    查看日志: tail -f $COMFYUI_DIR/comfyui.log"
    echo "    停止服务: pkill -f 'python3 main.py'"
    echo ""
}

# 主菜单
main() {
    echo "=========================================="
    echo "  漫AI - Wan2.1 启动器"
    echo "=========================================="
    echo ""
    echo "选择操作:"
    echo "  1) 安装依赖 & 下载模型"
    echo "  2) 仅启动服务"
    echo "  3) 检查GPU状态"
    echo "  4) 查看日志"
    echo "  0) 退出"
    echo ""
    read -p "请输入选项 [1-4]: " choice
    
    case $choice in
        1)
            check_gpu
            install_deps
            download_model
            start_comfyui
            show_status
            ;;
        2)
            start_comfyui
            show_status
            ;;
        3)
            check_gpu
            ;;
        4)
            if [ -f "$COMFYUI_DIR/comfyui.log" ]; then
                tail -f "$COMFYUI_DIR/comfyui.log"
            else
                log_error "日志文件不存在"
            fi
            ;;
        0)
            exit 0
            ;;
        *)
            log_error "无效选项"
            exit 1
            ;;
    esac
}

# 如果直接运行此脚本
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
