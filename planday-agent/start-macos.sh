#!/bin/bash

# =============================================================================
# PlanDay macOS 专用启动脚本
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 打印横幅
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🍎 PlanDay for macOS                       ║"
    echo "║                  AI 智能日程助手 - 一键启动                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] ℹ️  $1${NC}"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 清理端口
cleanup_port() {
    local port=$1
    local service_name=$2
    
    if check_port $port; then
        warn "$service_name 端口 $port 被占用，正在清理..."
        local pids=$(lsof -ti:$port)
        for pid in $pids; do
            kill -9 $pid 2>/dev/null || true
        done
        sleep 2
    fi
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."
    
    # 检查 Python3
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        echo "请安装 Python 3.8+: https://www.python.org/downloads/"
        exit 1
    fi
    
    # 检查 uv
    if ! command -v uv &> /dev/null; then
        warn "uv 未安装，正在安装..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        if ! command -v uv &> /dev/null; then
            error "uv 安装失败"
            exit 1
        fi
    fi
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js 未安装"
        echo "请安装 Node.js 16+: https://nodejs.org/"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        error "npm 未安装，请重新安装 Node.js"
        exit 1
    fi
    
    log "✅ 所有依赖检查通过"
}

# 设置环境变量
setup_environment() {
    log "设置环境变量..."
    
    # 设置默认环境变量
    export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-zUbEOQKhP8qYdpBx3542494939Fe4bAf95Fd195c906d8695}"
    export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://free.v36.cm/v1}"
    export MODEL_NAME="${MODEL_NAME:-gpt-4o-mini}"
    
    log "✅ 环境变量设置完成"
}

# 安装后端依赖
install_backend_deps() {
    log "检查后端依赖..."
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "pyproject.toml" ]]; then
        error "pyproject.toml 未找到"
        exit 1
    fi
    
    # 检查虚拟环境
    if [[ ! -d ".venv" ]]; then
        log "创建虚拟环境..."
        uv sync
    else
        log "虚拟环境已存在"
    fi
    
    log "✅ 后端依赖检查完成"
}

# 安装前端依赖
install_frontend_deps() {
    log "检查前端依赖..."
    cd "$FRONTEND_DIR"
    
    if [[ ! -f "package.json" ]]; then
        error "package.json 未找到"
        exit 1
    fi
    
    if [[ ! -d "node_modules" ]]; then
        log "安装前端依赖..."
        npm install
    else
        log "前端依赖已存在"
    fi
    
    log "✅ 前端依赖检查完成"
}

# 启动后端服务
start_backend() {
    log "启动后端服务..."
    cd "$PROJECT_ROOT"
    
    # 清理后端端口
    cleanup_port 8000 "后端"
    
    # 启动后端HTTP服务器
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    nohup uv run python server.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"
    
    # 等待后端启动
    log "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8000 >/dev/null 2>&1; then
            log "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    error "后端服务启动超时"
    cat "$PROJECT_ROOT/logs/backend.log"
    exit 1
}

# 启动前端服务
start_frontend() {
    log "启动前端服务..."
    cd "$FRONTEND_DIR"
    
    # 清理前端端口
    cleanup_port 3000 "前端"
    
    # 设置环境变量禁止自动打开浏览器
    export BROWSER=none
    
    # 启动前端
    nohup npm start > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"
    
    # 等待前端启动
    log "等待前端服务启动..."
    for i in {1..60}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            log "✅ 前端服务启动成功 (PID: $FRONTEND_PID)"
            return 0
        fi
        sleep 1
    done
    
    error "前端服务启动超时"
    cat "$PROJECT_ROOT/logs/frontend.log"
    exit 1
}

# 清理函数
cleanup() {
    log "正在停止服务..."
    
    # 停止后端
    if [[ -f "$PROJECT_ROOT/.backend.pid" ]]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/.backend.pid")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            kill "$BACKEND_PID"
            log "后端服务已停止"
        fi
        rm -f "$PROJECT_ROOT/.backend.pid"
    fi
    
    # 停止前端
    if [[ -f "$PROJECT_ROOT/.frontend.pid" ]]; then
        FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            kill "$FRONTEND_PID"
            log "前端服务已停止"
        fi
        rm -f "$PROJECT_ROOT/.frontend.pid"
    fi
    
    # 清理端口
    cleanup_port 8000 "后端"
    cleanup_port 3000 "前端"
    
    log "✅ 清理完成"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 主函数
main() {
    print_banner
    
    check_dependencies
    setup_environment
    install_backend_deps
    install_frontend_deps
    
    start_backend
    start_frontend
    
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                     🎉 启动成功！                              ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  🌐 前端地址: ${CYAN}http://localhost:3000${GREEN}                        ║${NC}"
    echo -e "${GREEN}║  📡 后端地址: ${CYAN}http://localhost:8000${GREEN}                        ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  📝 查看日志:                                                  ║${NC}"
    echo -e "${GREEN}║     tail -f logs/backend.log                                 ║${NC}"
    echo -e "${GREEN}║     tail -f logs/frontend.log                                ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  🛑 停止服务: 按 ${RED}Ctrl+C${GREEN}                                    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # 自动打开浏览器
    sleep 2
    if command -v open >/dev/null 2>&1; then
        log "正在打开浏览器..."
        open http://localhost:3000
    fi
    
    # 保持脚本运行
    log "服务正在运行中，按 Ctrl+C 停止..."
    while true; do
        sleep 5
        
        # 检查服务状态
        if [[ -f "$PROJECT_ROOT/.backend.pid" ]]; then
            BACKEND_PID=$(cat "$PROJECT_ROOT/.backend.pid")
            if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
                error "后端服务意外停止"
                break
            fi
        fi
        
        if [[ -f "$PROJECT_ROOT/.frontend.pid" ]]; then
            FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
            if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
                error "前端服务意外停止"
                break
            fi
        fi
    done
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi