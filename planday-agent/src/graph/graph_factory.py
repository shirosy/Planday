"""
Graph Factory for creating a router-based PlanDay agent.
This version implements a robust, multi-tool-agent using a router to classify
user intent and direct the request to the appropriate specialized tool agent.
"""
from typing import Literal, Optional
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic.v1 import BaseModel, Field
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.state.schemas import GlobalState
from src.tools import (
    calendar_tools_list,
    initialize_calendar_tools,
    initialize_parser,
    initialize_planner,
    initialize_task_tools,
    parser_tools_list,
    planning_tools_list,
    task_tools_list,
    MCPToolManager,
)
from src.utils.llm_manager import LLMManager

class Router(BaseModel):
    """Route the user's request to the appropriate agent."""
    route: Literal["calendar", "task", "planning", "parser", "general"] = Field(
        ...,
        description="Given the user's request, decide which agent is best suited to handle it."
    )

def should_continue(state: GlobalState) -> Literal["tools", "__end__"]:
    """Determines the next step after a tool-calling model has been invoked."""
    messages = state.get('messages', [])
    last_message = messages[-1] if messages else None
    
    # 如果最后一条消息有工具调用，执行工具
    if last_message and getattr(last_message, 'tool_calls', None):
        return "tools"
    
    # 否则结束对话
    return "__end__"

class GraphFactory:
    """Factory to create the LangGraph-powered agent."""

    def __init__(self, llm_manager: LLMManager, mcp_tools: MCPToolManager):
        # Initialize all toolsets
        initialize_calendar_tools(mcp_tools, llm_manager)
        initialize_task_tools(mcp_tools, llm_manager)
        initialize_planner(llm_manager, mcp_tools)
        initialize_parser(llm_manager)

        # Create specialized LLMs and ToolNodes for each agent
        self.calendar_agent = llm_manager.client.bind_tools(calendar_tools_list)
        self.calendar_tool_node = ToolNode(calendar_tools_list)

        self.task_agent = llm_manager.client.bind_tools(task_tools_list)
        self.task_tool_node = ToolNode(task_tools_list)
        
        self.planning_agent = llm_manager.client.bind_tools(planning_tools_list)
        self.planning_tool_node = ToolNode(planning_tools_list)

        self.parser_agent = llm_manager.client.bind_tools(parser_tools_list)
        self.parser_tool_node = ToolNode(parser_tools_list)
        
        self.general_agent = llm_manager.client

        # Create the router LLM
        self.router_llm = llm_manager.client.with_structured_output(Router)

    async def route_request(self, state: GlobalState) -> dict:
        """The entry point of the graph. Routes the request to the correct agent."""
        messages = state.get('messages', [])
        user_input = messages[-1].content
        
        # 添加详细的路由提示
        routing_prompt = f"""
        用户请求: {user_input}
        
        请根据以下规则选择最适合的agent:
        
        - "calendar": 查询、创建、修改、删除日程事件。关键词：安排会议、查看日程、今天的安排、明天几点、会议
        - "task": 管理待办事项和任务。关键词：创建任务、完成任务、删除任务、我的待办、任务列表
        - "planning": 时间规划、空闲时间查找、任务分解、时间建议。关键词：空闲时间、时间安排、规划、分解任务、找时间、几小时、时间块
        - "parser": 解析复杂的时间表达式和日期。关键词：解析日期、时间格式
        - "general": 一般对话、问候、无明确意图的请求
        
        特别注意：
        - 如果用户询问"空闲时间"、"找时间"、"几小时"等，应该选择 "planning"
        - 如果用户要查看已有的日程安排，应该选择 "calendar"
        """
        
        route = await self.router_llm.ainvoke([HumanMessage(content=routing_prompt)])
        
        return {"route_decision": route.route}

    async def call_calendar_agent(self, state: GlobalState):
        """Invokes the calendar agent with the user's request."""
        messages = state['messages']
        
        # Add calendar-specific system message with current date
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_year = datetime.now().year
        
        calendar_system_message = SystemMessage(content=f"""
        你是一个专业的日历管理助手。当前日期是 {current_date}，当前年份是 {current_year}。

        重要的时间解析规则：
        1. **当前年份**: {current_year} - 所有日期必须基于当前年份
        2. **相对时间解析**:
           - "明天" = {current_date} 的下一天，年份是 {current_year}
           - "后天" = {current_date} 的后两天，年份是 {current_year}
           - "下周" = 基于 {current_date} 计算，年份是 {current_year}
        3. **具体日期解析**:
           - "8月6日" = {current_year}-08-06
           - "12月25日" = {current_year}-12-25
        4. **时间格式**: 
           - 使用24小时制
           - 上午10点 = 10:00
           - 下午3点 = 15:00
           - 晚上8点 = 20:00

        在调用工具时，确保传递正确的年份和时间格式。所有时间都应该基于当前年份 {current_year}。
        """)
        
        # Add system message to the beginning of the conversation
        enhanced_messages = [calendar_system_message] + messages
        
        response = await self.calendar_agent.ainvoke(enhanced_messages)
        return {"messages": [response]}

    async def call_task_agent(self, state: GlobalState):
        """Invokes the task agent with the user's request."""
        response = await self.task_agent.ainvoke(state['messages'])
        return {"messages": [response]}

    async def call_planning_agent(self, state: GlobalState):
        """Invokes the planning agent with the user's request."""
        messages = state['messages']
        
        # 为规划代理添加专门的系统提示
        planning_system_message = SystemMessage(content="""
        你是一个专业的时间规划助手。当用户询问空闲时间、时间安排、任务分解等时，你需要：

        1. **空闲时间查询**：如果用户询问空闲时间（如"找出本周2小时的空闲时间"），使用 find_free_time 工具
        2. **时间建议**：如果用户需要为特定任务安排时间，使用 suggest_task_time 工具
        3. **任务分解**：如果用户有复杂项目需要分解，使用 decompose_task_into_steps 工具
        4. **快速安排**：如果用户有多个任务需要安排，使用 quick_schedule_tasks 工具

        重要提醒：
        - 当用户说"找出本周X小时的空闲时间"时，一定要使用 find_free_time 工具
        - 从用户请求中提取时间长度（如"2小时"=2.0），天数范围（如"本周"=7天）
        - 优先使用工具而不是直接回答
        """)
        
        # 将系统消息添加到对话开头
        enhanced_messages = [planning_system_message] + messages
        
        response = await self.planning_agent.ainvoke(enhanced_messages)
        return {"messages": [response]}

    async def call_parser_agent(self, state: GlobalState):
        """Invokes the parser agent with the user's request."""
        response = await self.parser_agent.ainvoke(state['messages'])
        return {"messages": [response]}

    async def call_general_agent(self, state: GlobalState):
        """Handles general conversation."""
        response = await self.general_agent.ainvoke(state['messages'])
        return {"messages": [response]}

    def create_graph(self, checkpointer=None):
        """Creates and compiles the main router-based agent graph."""
        builder = StateGraph(GlobalState)

        builder.add_node("router", self.route_request)
        
        builder.add_node("calendar_agent", self.call_calendar_agent)
        builder.add_node("calendar_tools", self.calendar_tool_node)

        builder.add_node("task_agent", self.call_task_agent)
        builder.add_node("task_tools", self.task_tool_node)

        builder.add_node("planning_agent", self.call_planning_agent)
        builder.add_node("planning_tools", self.planning_tool_node)

        builder.add_node("parser_agent", self.call_parser_agent)
        builder.add_node("parser_tools", self.parser_tool_node)

        builder.add_node("general_agent", self.call_general_agent)

        builder.set_entry_point("router")

        builder.add_conditional_edges(
            "router",
            lambda x: x["route_decision"],
            {
                "calendar": "calendar_agent",
                "task": "task_agent",
                "planning": "planning_agent",
                "parser": "parser_agent",
                "general": "general_agent",
            }
        )

        builder.add_conditional_edges("calendar_agent", should_continue, {"tools": "calendar_tools", "__end__": END})
        builder.add_edge("calendar_tools", END)  # 工具执行后直接结束

        builder.add_conditional_edges("task_agent", should_continue, {"tools": "task_tools", "__end__": END})
        builder.add_edge("task_tools", END)  # 工具执行后直接结束

        builder.add_conditional_edges("planning_agent", should_continue, {"tools": "planning_tools", "__end__": END})
        builder.add_edge("planning_tools", END)  # 工具执行后直接结束

        builder.add_conditional_edges("parser_agent", should_continue, {"tools": "parser_tools", "__end__": END})
        builder.add_edge("parser_tools", END)  # 工具执行后直接结束

        builder.add_edge("general_agent", END)

        return builder.compile(
            checkpointer=checkpointer,
            debug=False  # 关闭debug模式减少日志
        )
