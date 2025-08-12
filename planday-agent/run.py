#!/usr/bin/env python3
"""
PlanDay Runner - 独立运行脚本
解决交互式输入和模块导入问题
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 导入主模块
from src.core.agent_supervisor import AgentSupervisorSystem

async def main():
    """主入口函数"""
    config = {}
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor() as executor:
        agent = AgentSupervisorSystem(config, executor)
        
        try:
            await agent.setup()
            print("🗓️ PlanDay Agent - Personal Scheduling Assistant")
            print("Type 'quit' to exit, 'help' for examples.\n")
            
            # 检查是否在交互式环境中
            if not sys.stdin.isatty():
                print("⚠️  Non-interactive environment detected. Please run in an interactive terminal.")
                print("💡 Tip: Try running 'python run.py' directly in your terminal")
                return
            
            session_id = "default-session"
            
            while True:
                try:
                    user_input = input("\n💬 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() == 'help':
                        print("📋 Available commands:")
                        print("• Schedule events: 'Schedule meeting tomorrow 2-3pm'")
                        print("• Create tasks: 'Add task to finish report by Friday'")
                        print("• Find time: 'Find 1 hour free time today'")
                        print("• View calendar: 'What's on my calendar today?'")
                        print("• history - Show conversation history")
                        print("• clear - Clear conversation history")
                        print("• quit/exit - Exit the application")
                        continue
                    
                    if user_input.lower() == 'history':
                        try:
                            history = await agent.get_conversation_history(session_id)
                            print(f"📊 Session: {history['session_id']}")
                            print(f"📈 Messages: {history['message_count']}")
                            if history.get('last_activity'):
                                print(f"🕒 Last activity: {history['last_activity']}")
                            print("💬 Recent messages:")
                            for i, msg in enumerate(history.get('messages', [])[-5:], 1):
                                print(f"  {i}. [{msg['type']}] {msg['content'][:100]}...")
                        except Exception as e:
                            print(f"❌ Error getting history: {e}")
                        continue
                        
                    if user_input.lower() == 'clear':
                        try:
                            success = await agent.clear_conversation(session_id)
                            if success:
                                print("🧹 Conversation history cleared!")
                            else:
                                print("❌ Failed to clear conversation")
                        except Exception as e:
                            print(f"❌ Error clearing conversation: {e}")
                        continue
                    
                    print("🤖 PlanDay: Processing...")
                    
                    try:
                        result = await asyncio.wait_for(agent.process_request(user_input, session_id), timeout=60.0)
                        if result.get('success'):
                            response = result.get('response', 'No response received')
                            print(f"🤖 PlanDay: {response}")
                        else:
                            print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    except asyncio.TimeoutError:
                        print("🤖 PlanDay: The request timed out. Please try again.")
                    except Exception as e:
                        print(f"❌ An error occurred: {e}")
                        
                except KeyboardInterrupt:
                    print("\n👋 Exiting...")
                    break
                except EOFError:
                    print("\n👋 End of input detected. Goodbye!")
                    break
                    
        except Exception as e:
            print(f"❌ Critical error on startup: {e}")
            print("🔧 Please check:")
            print("1. Environment variables (.env file)")
            print("2. MCP server paths") 
            print("3. Calendar/Reminders permissions")
        finally:
            await agent.close()

if __name__ == "__main__":
    # 设置环境变量默认值
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'sk-zUbEOQKhP8qYdpBx3542494939Fe4bAf95Fd195c906d8695'
    if not os.getenv('OPENAI_BASE_URL'):
        os.environ['OPENAI_BASE_URL'] = 'https://free.v36.cm/v1'
    if not os.getenv('MODEL_NAME'):
        os.environ['MODEL_NAME'] = 'gpt-4o-mini'
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")