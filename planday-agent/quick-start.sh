#!/bin/bash

# =============================================================================
# PlanDay 快速启动脚本 (简化版)
# =============================================================================

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 PlanDay 快速启动中...${NC}"

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置环境变量
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-zUbEOQKhP8qYdpBx3542494939Fe4bAf95Fd195c906d8695}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://free.v36.cm/v1}"
export MODEL_NAME="${MODEL_NAME:-gpt-4o-mini}"

echo -e "${GREEN}✅ 环境变量已设置${NC}"

# 启动后端
echo -e "${BLUE}📡 启动后端服务...${NC}"
cd "$PROJECT_ROOT"
uv run python server.py &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端
echo -e "${BLUE}🌐 启动前端服务...${NC}"
cd "$PROJECT_ROOT/frontend"
npm start &
FRONTEND_PID=$!

# 等待前端启动
echo -e "${YELLOW}⏳ 等待服务启动完成...${NC}"
sleep 15

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║            🎉 启动完成！                  ║"
echo "║                                          ║"
echo "║  前端: http://localhost:3000             ║"
echo "║  后端: http://localhost:8000             ║"
echo "║                                          ║"
echo "║  按 Ctrl+C 停止所有服务                   ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 保持脚本运行
wait