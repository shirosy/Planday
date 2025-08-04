# PlanDay

基于 LangGraph 的智能日程和任务管理助手，支持自然语言交互，集成 macOS 日历和提醒事项应用。

## 核心功能

- **智能日历管理** - 自然语言创建事件，智能冲突解决，模糊搜索
- **任务管理** - 完整的任务增删改查，智能优先级推荐，工作量分析
- **智能规划** - 任务分解，时间段建议，空闲时间检测
- **图像解析** - 从图片中提取任务和事件信息
- **多代理架构** - LangGraph 实现，状态持久化，错误恢复

## 技术架构

```
PlanDay/
├── src/                    # 源代码
│   ├── graph/              # LangGraph 图实现
│   ├── tools/              # 代理工具集
│   │   ├── calendar_tools.py  # 日历工具 (6个)
│   │   ├── task_tools.py      # 任务工具 (7个)
│   │   ├── planning_tools.py  # 规划工具 (4个)
│   │   └── parser_tools.py    # 解析工具 (1个)
│   ├── utils/              # 核心工具
│   ├── state/              # 数据模式
│   └── core/               # 系统核心
├── mcp/                    # MCP 服务器
│   ├── mcp-ical/          # 日历服务
│   └── apple-reminders-mcp/  # 提醒事项服务
└── frontend/               # 前端界面
```

## 快速开始

### 环境要求

- macOS 系统
- Python 3.11+
- Node.js
- uv 包管理器

### 安装

1. 安装 Python 依赖
```bash
uv sync
```

2. 构建 MCP 服务器
```bash
cd mcp/apple-reminders-mcp-main && npm install && npm run build
cd ../mcp-ical && uv sync
```

3. 配置权限 - 授予终端访问日历和提醒事项的权限

### 使用

```bash
uv run python -m src.main
```

### 示例对话

```
"明天下午3点安排项目评审会议"
"这周的日程安排是什么？"
"添加一个任务：周五前完成季度报告"
"帮我把'启动新网站'分解成具体步骤"
"分析这张白板图片，提取其中的任务"
```

## 核心算法

- **加权区间调度算法** - 基于优先级和持续时间优化日程安排
- **优先级评分系统** - 智能任务优先级分配和推荐
- **时间复杂度**: O(n²) 动态规划算法

## 工具集

### 日历工具 (6个)
创建、查询、更新、删除事件，模糊搜索，智能冲突解决

### 任务工具 (7个)  
任务CRUD操作，完成任务，优先级推荐，工作量分析

### 规划工具 (4个)
任务分解，时间建议，快速调度，空闲时间查找

### 解析工具 (1个)
从图片URL提取任务和事件信息

## 环境配置

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=your_base_url  # 可选
```

## 许可证

MIT License