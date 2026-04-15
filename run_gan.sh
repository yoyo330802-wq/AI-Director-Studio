#!/usr/bin/env bash
# GAN Auto-Runner 一键运行脚本
# 用法: ./run_gan.sh [--workspace PATH] [--mode auto|manual] [--resume-from PHASE] [--sprint S1] [--reset]

set -e

WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
MODE="auto"
RESUME_FROM=""
SPRINT="S1"
RESET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace|-w)
            WORKSPACE="$2"; shift 2 ;;
        --mode|-m)
            MODE="$2"; shift 2 ;;
        --resume-from|-r)
            RESUME_FROM="--resume-from $2"; shift 2 ;;
        --sprint|-s)
            SPRINT="$2"; shift 2 ;;
        --reset)
            RESET=true; shift ;;
        *)
            echo "未知参数: $1"; exit 1 ;;
    esac
done

cd "$WORKSPACE"

echo ""
echo "═══════════════════════════════════════════"
echo "🚀 GAN Auto-Runner"
echo "   工作空间: $WORKSPACE"
echo "   模式: $MODE"
echo "   Sprint: $SPRINT"
echo "═══════════════════════════════════════════"
echo ""

# 检查 Python 依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 未安装"
    exit 1
fi

# 检查 pyyaml
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "📦 安装 pyyaml..."
    pip install pyyaml -q
fi

# 执行
if [ "$RESET" = true ]; then
    python3 "$WORKSPACE/gan-auto-runner/gan_runner.py" \
        --workspace "$WORKSPACE" \
        --mode "$MODE" \
        --sprint "$SPRINT" \
        --reset \
        $RESUME_FROM
else
    python3 "$WORKSPACE/gan-auto-runner/gan_runner.py" \
        --workspace "$WORKSPACE" \
        --mode "$MODE" \
        --sprint "$SPRINT" \
        $RESUME_FROM
fi
