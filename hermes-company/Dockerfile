# Hermes Agent Docker 镜像
FROM python:3.11-slim

# 安装基础工具
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Claude CLI 安装（预留，可后续按需启用）
# RUN pip install claude-code 2>/dev/null || true

# 设置工作目录
WORKDIR /workspace

# 默认命令
CMD ["claude", "--help"]
