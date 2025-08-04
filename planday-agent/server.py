#!/usr/bin/env python3
"""
PlanDay HTTP 服务器
为前端提供 HTTP API 接口
"""

import sys
import os
import asyncio
import json
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.core.agent_supervisor import AgentSupervisorSystem

# 初始化 FastAPI 应用
app = FastAPI(
    title="PlanDay API",
    description="AI 智能日程助手 HTTP API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
agent_system: Optional[AgentSupervisorSystem] = None
executor: Optional[ThreadPoolExecutor] = None

# 请求模型
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    error: Optional[str] = None
    events: Optional[list] = None
    tasks: Optional[list] = None
    recommendations: Optional[list] = None

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 Agent 系统"""
    global agent_system, executor
    
    print("🚀 正在启动 PlanDay HTTP 服务器...")
    
    # 设置环境变量默认值
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'sk-zUbEOQKhP8qYdpBx3542494939Fe4bAf95Fd195c906d8695'
    if not os.getenv('OPENAI_BASE_URL'):
        os.environ['OPENAI_BASE_URL'] = 'https://free.v36.cm/v1'
    if not os.getenv('MODEL_NAME'):
        os.environ['MODEL_NAME'] = 'gpt-4o-mini'
    
    try:
        executor = ThreadPoolExecutor()
        config = {}
        agent_system = AgentSupervisorSystem(config, executor)
        await agent_system.setup()
        print("✅ PlanDay Agent 系统初始化完成")
        print("🌐 HTTP API 服务器已启动在 http://localhost:8000")
    except Exception as e:
        print(f"❌ Agent 系统初始化失败: {e}")
        raise e

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global agent_system, executor
    
    print("🛑 正在关闭 PlanDay HTTP 服务器...")
    
    if agent_system:
        await agent_system.close()
    
    if executor:
        executor.shutdown(wait=True)
    
    print("✅ 资源清理完成")

# 健康检查端点
@app.get("/")
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "PlanDay API 服务器运行正常",
        "version": "1.0.0"
    }

# 聊天端点
@app.post("/api/chat")
async def chat_endpoint(
    message: str = Form(...),
    session_id: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """处理聊天请求"""
    global agent_system
    
    if not agent_system:
        raise HTTPException(status_code=500, detail="Agent 系统未初始化")
    
    try:
        # 处理图片（如果有）
        image_data = None
        if image:
            image_content = await image.read()
            image_data = base64.b64encode(image_content).decode()
        
        # 处理请求
        result = await asyncio.wait_for(
            agent_system.process_request(message, session_id), 
            timeout=60.0
        )
        
        if result.get('success'):
            return JSONResponse(content={
                "response": result.get('response', ''),
                "session_id": session_id,
                "success": True,
                "events": result.get('events', []),
                "tasks": result.get('tasks', []),
                "recommendations": result.get('recommendations', [])
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "response": "",
                    "session_id": session_id,
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                }
            )
            
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=408,
            content={
                "response": "",
                "session_id": session_id,
                "success": False,
                "error": "请求超时，请重试"
            }
        )
    except Exception as e:
        print(f"❌ 聊天请求处理错误: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "response": "",
                "session_id": session_id,
                "success": False,
                "error": f"处理请求时出错: {str(e)}"
            }
        )

# 历史记录端点
@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    global agent_system
    
    if not agent_system:
        raise HTTPException(status_code=500, detail="Agent 系统未初始化")
    
    try:
        history = await agent_system.get_conversation_history(session_id)
        return JSONResponse(content=history)
    except Exception as e:
        print(f"❌ 获取历史记录错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

# 清除历史端点
@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str):
    """清除会话历史"""
    global agent_system
    
    if not agent_system:
        raise HTTPException(status_code=500, detail="Agent 系统未初始化")
    
    try:
        success = await agent_system.clear_conversation(session_id)
        return JSONResponse(content={"success": success})
    except Exception as e:
        print(f"❌ 清除历史记录错误: {e}")
        raise HTTPException(status_code=500, detail=f"清除历史记录失败: {str(e)}")

# 图片上传端点
@app.post("/api/upload")
async def upload_image(image: UploadFile = File(...)):
    """处理图片上传"""
    try:
        # 这里可以添加图片处理逻辑
        # 目前简单返回成功响应
        return JSONResponse(content={
            "url": f"data:image/jpeg;base64,{base64.b64encode(await image.read()).decode()}",
            "description": "图片上传成功"
        })
    except Exception as e:
        print(f"❌ 图片上传错误: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 启动 PlanDay HTTP 服务器...")
    
    # 运行服务器
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()