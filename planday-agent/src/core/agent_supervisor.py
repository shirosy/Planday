"""
Agent Supervisor System - The main entry point for processing user requests.
This version is aligned with LangGraph's best practices, using a checkpointer
for automatic state management and persistence.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import aiosqlite
import structlog

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.runnables import Runnable

from src.state.schemas import GlobalState
from src.graph.graph_factory import GraphFactory
from src.utils.llm_manager import LLMManager
from src.tools import MCPToolManager

logger = structlog.get_logger()

class AgentSupervisorSystem:
    """
    Orchestrates the LangGraph-based agent, leveraging a checkpointer for
    robust, persistent state management across conversation turns.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, executor=None):
        """
        Initializes the system components but defers graph compilation until
        the async setup is complete.
        """
        self.config = config or {}
        self.executor = executor
        from pathlib import Path
        self.llm_manager = LLMManager(self.config.get("llm", {}))

        # 根据当前文件位置动态计算项目根目录，确保即使移动项目也能正常解析路径
        project_root = Path(__file__).resolve().parents[2]
        calendar_path = project_root / "mcp" / "mcp-ical"
        reminders_path = project_root / "mcp" / "apple-reminders-mcp-main"

        self.mcp_tools = MCPToolManager(
            calendar_server_path=str(calendar_path),
            reminders_server_path=str(reminders_path),
            executor=self.executor
        )
        self.factory = GraphFactory(self.llm_manager, self.mcp_tools)
        self.graph: Optional[Runnable] = None
        self.checkpointer: Optional[AsyncSqliteSaver] = None
        self.db_conn: Optional[aiosqlite.Connection] = None

    async def setup(self):
        """
        Asynchronously sets up the database connection, checkpointer, and
        compiles the graph. This must be called before processing requests.
        """
        if self.graph:
            return
            
        # Connect to the SQLite database asynchronously
        self.db_conn = await aiosqlite.connect("checkpoints.sqlite")
        self.checkpointer = AsyncSqliteSaver(conn=self.db_conn)
        
        # Compile the graph with persistence enabled
        self.graph = self.factory.create_graph(checkpointer=self.checkpointer)
        logger.info("Agent Supervisor System setup complete.")

    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves the conversation history for a session.
        """
        if not self.graph:
            raise RuntimeError("System not set up. Please call 'setup()' before accessing history.")
        
        try:
            graph_config = {"configurable": {"thread_id": session_id}}
            state = await self.graph.aget_state(graph_config)
            
            if state and state.values:
                messages = state.values.get('messages', [])
                return {
                    "session_id": session_id,
                    "message_count": len(messages),
                    "last_activity": state.values.get('last_activity'),
                    "conversation_summary": state.values.get('conversation_summary'),
                    "messages": [
                        {
                            "type": type(msg).__name__,
                            "content": getattr(msg, 'content', str(msg)),
                            "timestamp": getattr(msg, 'additional_kwargs', {}).get('timestamp')
                        } for msg in messages
                    ]
                }
            else:
                return {"session_id": session_id, "message_count": 0, "messages": []}
                
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return {"session_id": session_id, "error": str(e)}

    async def clear_conversation(self, session_id: str) -> bool:
        """
        Clears the conversation history for a session.
        """
        if not self.checkpointer:
            return False
            
        try:
            # Clear the state for this session
            graph_config = {"configurable": {"thread_id": session_id}}
            # Note: LangGraph doesn't have a direct clear method, 
            # but we can overwrite with empty state
            empty_state = {"messages": []}
            await self.graph.ainvoke(empty_state, graph_config)
            logger.info(f"Cleared conversation for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False

    async def close(self):
        """
        Gracefully closes the database connection.
        """
        if self.db_conn:
            await self.db_conn.close()
            logger.info("Database connection closed.")

    async def process_request(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """
        Processes a user request by invoking the compiled agent graph with proper conversation continuity.
        """
        if not self.graph:
            raise RuntimeError("System not set up. Please call 'setup()' before processing requests.")

        try:
            logger.info("Processing user request", session_id=session_id)
            
            # Use the actual session_id for conversation continuity
            graph_config = {"configurable": {"thread_id": session_id}}
            
            # Create the new user message
            user_message = HumanMessage(content=user_input)
            
            # Get the current state from checkpointer to maintain conversation history
            try:
                current_state = await self.graph.aget_state(graph_config)
                if current_state and current_state.values and current_state.values.get('messages'):
                    # Append new message to existing conversation
                    updated_state = {
                        "messages": current_state.values['messages'] + [user_message],
                        "route_decision": current_state.values.get('route_decision'),
                        "user_context": current_state.values.get('user_context', {}),
                        "conversation_summary": current_state.values.get('conversation_summary'),
                        "last_activity": datetime.now(),
                        "message_count": len(current_state.values['messages']) + 1
                    }
                else:
                    # First message in conversation
                    updated_state = {
                        "messages": [user_message],
                        "last_activity": datetime.now(),
                        "message_count": 1
                    }
            except Exception as e:
                logger.warning(f"Could not retrieve state for session {session_id}, starting fresh: {e}")
                # Fallback to new conversation if state retrieval fails
                updated_state = {
                    "messages": [user_message],
                    "last_activity": datetime.now(),
                    "message_count": 1
                }
            
            # Check message count and truncate if necessary (keep last 20 messages)
            if len(updated_state["messages"]) > 20:
                # Keep system messages and clean recent history
                system_messages = [msg for msg in updated_state["messages"] if hasattr(msg, 'type') and msg.type == 'system']
                
                # Get recent messages, ensuring we don't break tool call chains
                recent_messages = updated_state["messages"][-19:]
                
                # Filter out orphaned tool messages that don't have corresponding tool calls
                cleaned_messages = []
                for i, msg in enumerate(recent_messages):
                    if hasattr(msg, 'type') and msg.type == 'tool':
                        # Check if previous message has tool_calls
                        if i > 0 and hasattr(recent_messages[i-1], 'tool_calls') and recent_messages[i-1].tool_calls:
                            cleaned_messages.append(msg)
                        # Skip orphaned tool messages
                    else:
                        cleaned_messages.append(msg)
                
                updated_state["messages"] = system_messages + cleaned_messages
                logger.info(f"Truncated and cleaned conversation history for session {session_id}")
            
            # Execute the graph with the updated state and recursion limit
            final_state = await self.graph.ainvoke(
                updated_state, 
                {
                    **graph_config,
                    "recursion_limit": 15  # 设置递归限制防止无限循环
                }
            )
            
            # Extract the final response
            response = "I have processed your request."  # Default response
            if final_state.get('messages'):
                last_message = final_state['messages'][-1]
                
                if isinstance(last_message, AIMessage):
                    response = last_message.content or response
                elif hasattr(last_message, 'content') and last_message.content:
                    response = last_message.content
            
            logger.info("Request processed successfully", session_id=session_id, 
                       message_count=len(final_state.get('messages', [])))
            
            return {
                "response": response,
                "success": True,
                "session_id": session_id,
                "message_count": len(final_state.get('messages', []))
            }
        except Exception as e:
            logger.error("Error processing request", session_id=session_id, error=str(e), exc_info=True)
            return {
                "response": "I'm sorry, an unexpected error occurred. Please try again later.",
                "success": False,
                "session_id": session_id,
                "error": str(e)
            }
