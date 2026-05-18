#!/bin/bash
# 灵枢创作引擎 - 部署脚本
# 用法: ./deploy.sh [ssh_host]  (默认 root@8.211.155.252)

SSH_HOST="${1:-root@8.211.155.252}"
SSH_KEY="$HOME/.ssh/candlelight_aliyun"
IMAGE="lingxu-engine:latest"

set -e

echo "==> 构建前端..."
cd "$(dirname "$0")/frontend"
npm run build

echo "==> 构建 Docker 镜像..."
cd "$(dirname "$0")"
docker build -t $IMAGE .

echo "==> 保存并传输镜像..."
docker save $IMAGE | gzip > /tmp/lingxu-engine.tar.gz
scp -i "$SSH_KEY" /tmp/lingxu-engine.tar.gz "$SSH_HOST:/tmp/"
rm /tmp/lingxu-engine.tar.gz

echo "==> 远程部署..."
ssh -i "$SSH_KEY" "$SSH_HOST" << 'EOF'
  docker load < /tmp/lingxu-engine.tar.gz
  rm /tmp/lingxu-engine.tar.gz

  # 停止旧容器
  docker stop lingxu 2>/dev/null || true
  docker rm lingxu 2>/dev/null || true

  # 启动新容器
  docker run -d \
    --name lingxu \
    --restart unless-stopped \
    -p 8001:8000 \
    lingxu-engine:latest

  echo "部署完成！http://8.211.155.252:8001"
EOF
