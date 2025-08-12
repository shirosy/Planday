#!/bin/bash

# =============================================================================
# PlanDay 一键启动脚本
# =============================================================================

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT"

# 日志文件
LOG_DIR="$PROJECT_ROOT/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# PID 文件
PID_DIR="$PROJECT_ROOT/.pids"
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"

# 创建必要的目录
mkdir -p "$LOG_DIR" "$PID_DIR"

# =============================================================================
# 工具函数
# =============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                      🚀 PlanDay 启动器                        ║"
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

success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] ℹ️  $1${NC}"
}

# =============================================================================
# 环境检查函数
# =============================================================================

check_dependencies() {
    log "检查系统依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装，请先安装 Python 3.8+"
        exit 1
    fi
    
    # 检查 uv
    if ! command -v uv &> /dev/null; then
        error "uv 未安装，请运行: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js 未安装，请先安装 Node.js 16+"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    success "所有依赖检查通过"
}

check_environment() {
    log "检查环境配置..."
    
    # 检查环境变量
    if [[ -z "$OPENAI_API_KEY" ]]; then
        warn "OPENAI_API_KEY 未设置，将使用默认配置"
    fi
    
    if [[ -z "$OPENAI_BASE_URL" ]]; then
        warn "OPENAI_BASE_URL 未设置，将使用默认配置"
    fi
    
    # 检查 MCP 服务器
    MCP_ICAL_PATH="$PROJECT_ROOT/mcp/mcp-ical"
    MCP_REMINDERS_DIR="$PROJECT_ROOT/mcp/apple-reminders-mcp-main"
    MCP_REMINDERS_PATH="$MCP_REMINDERS_DIR/build/index.js"
    
    if [[ ! -d "$MCP_ICAL_PATH" ]]; then
        warn "MCP iCal 服务器未找到: $MCP_ICAL_PATH"
    fi
    
    # 检查并构建 Reminders MCP
    if [[ ! -f "$MCP_REMINDERS_PATH" ]]; then
        warn "MCP Reminders 服务器构建文件未找到: $MCP_REMINDERS_PATH"
        info "正在尝试构建 Reminders MCP..."
        cd "$MCP_REMINDERS_DIR"
        if [[ ! -d "node_modules" ]]; then
            log "正在安装 Reminders MCP 依赖..."
            npm install || {
                error "Reminders MCP 依赖安装失败"
                exit 1
            }
        fi
        log "正在构建 Reminders MCP..."
        npm run build || {
            error "Reminders MCP 构建失败"
            exit 1
        }
        cd "$PROJECT_ROOT"
        success "Reminders MCP 构建完成"
    fi
    
    success "环境配置检查完成"
}

# =============================================================================
# 清理函数
# =============================================================================

cleanup() {
    log "正在停止服务..."
    
    # 停止后端
    if [[ -f "$BACKEND_PID" ]]; then
        BACKEND_PID_NUM=$(cat "$BACKEND_PID")
        if kill -0 "$BACKEND_PID_NUM" 2>/dev/null; then
            kill "$BACKEND_PID_NUM"
            success "后端服务已停止"
        fi
        rm -f "$BACKEND_PID"
    fi
    
    # 停止前端
    if [[ -f "$FRONTEND_PID" ]]; then
        FRONTEND_PID_NUM=$(cat "$FRONTEND_PID")
        if kill -0 "$FRONTEND_PID_NUM" 2>/dev/null; then
            kill "$FRONTEND_PID_NUM"
            success "前端服务已停止"
        fi
        rm -f "$FRONTEND_PID"
    fi
    
    # 清理端口
    pkill -f "uv run python server.py" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
    
    success "清理完成"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# =============================================================================
# 安装依赖函数
# =============================================================================

install_backend_deps() {
    log "安装后端依赖..."
    cd "$BACKEND_DIR"
    
    if [[ ! -f "pyproject.toml" ]]; then
        error "pyproject.toml 未找到，请确认在正确的项目目录"
        exit 1
    fi
    
    uv sync || {
        error "后端依赖安装失败"
        exit 1
    }
    
    success "后端依赖安装完成"
}

install_frontend_deps() {
    log "安装前端依赖..."
    cd "$FRONTEND_DIR"
    
    if [[ ! -f "package.json" ]]; then
        error "package.json 未找到，请确认前端目录存在"
        exit 1
    fi
    
    if [[ ! -d "node_modules" ]] || [[ ! -f "package-lock.json" ]]; then
        pnpm install || {
            error "前端依赖安装失败"
            exit 1
        }
    else
        info "前端依赖已存在，跳过安装"
    fi
    
    success "前端依赖检查完成"
}

# =============================================================================
# 启动服务函数
# =============================================================================

start_backend() {
    log "启动后端服务..."
    cd "$BACKEND_DIR"
    
    # 设置默认环境变量
    export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-zUbEOQKhP8qYdpBx3542494939Fe4bAf95Fd195c906d8695}"
    export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://free.v36.cm/v1}"
    export MODEL_NAME="${MODEL_NAME:-gpt-4o-mini}"
    
    # 启动后端（后台运行）
    nohup uv run python server.py > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID_NUM=$!
    echo "$BACKEND_PID_NUM" > "$BACKEND_PID"
    
    # 等待后端启动
    sleep 3
    
    if kill -0 "$BACKEND_PID_NUM" 2>/dev/null; then
        success "后端服务已启动 (PID: $BACKEND_PID_NUM)"
        info "后端日志: $BACKEND_LOG"
        info "后端地址: http://localhost:8000"
    else
        error "后端服务启动失败，请检查日志: $BACKEND_LOG"
        exit 1
    fi
}

start_frontend() {
    log "启动前端服务..."
    cd "$FRONTEND_DIR"
    
    # 启动前端（后台运行）
    nohup pnpm start > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID_NUM=$!
    echo "$FRONTEND_PID_NUM" > "$FRONTEND_PID"
    
    # 等待前端启动
    log "等待前端服务启动..."
    sleep 10
    
    if kill -0 "$FRONTEND_PID_NUM" 2>/dev/null; then
        success "前端服务已启动 (PID: $FRONTEND_PID_NUM)"
        info "前端日志: $FRONTEND_LOG"
        info "前端地址: http://localhost:3000"
    else
        error "前端服务启动失败，请检查日志: $FRONTEND_LOG"
        exit 1
    fi
}

# =============================================================================
# 状态检查函数
# =============================================================================

check_services() {
    log "检查服务状态..."
    
    # 检查后端
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "后端服务运行正常 ✓"
    else
        warn "后端服务可能未完全启动，请稍等或检查日志"
    fi
    
    # 检查前端
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        success "前端服务运行正常 ✓"
    else
        warn "前端服务可能未完全启动，请稍等几秒后访问"
    fi
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    print_banner
    
    log "开始启动 PlanDay 应用..."
    
    # 检查依赖
    check_dependencies
    check_environment
    
    # 安装依赖
    install_backend_deps
    install_frontend_deps
    
    # 启动服务
    start_backend
    start_frontend
    
    # 检查服务状态
    sleep 5
    check_services
    
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                     🎉 启动成功！                              ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  前端地址: ${CYAN}http://localhost:3000${GREEN}                         ║${NC}"
    echo -e "${GREEN}║  后端地址: ${CYAN}http://localhost:8000${GREEN}                         ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  📝 后端日志: ${YELLOW}tail -f $BACKEND_LOG${GREEN}"
    echo -e "${GREEN}║  📝 前端日志: ${YELLOW}tail -f $FRONTEND_LOG${GREEN}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  按 ${RED}Ctrl+C${GREEN} 停止所有服务                                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # 保持脚本运行，等待用户中断
    log "服务正在运行中，按 Ctrl+C 停止..."
    wait
}

# =============================================================================
# 脚本入口
# =============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi