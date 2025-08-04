
from datetime import datetime
from typing import List, Optional

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.state.schemas import Task, CalendarEvent
from src.utils.llm_manager import LLMManager

# Module-level LLM manager, to be initialized by the GraphFactory.
llm_manager_instance: Optional[LLMManager] = None

def initialize_parser(llm_manager: LLMManager):
    """Initializes the module-level LLM manager for the parser tool."""
    global llm_manager_instance
    llm_manager_instance = llm_manager

class ImageParseInput(BaseModel):
    image_url: str = Field(description="The public URL of the image to be parsed.")

class ParsedImageContent(BaseModel):
    """Structured format for content extracted from an image."""
    events: List[CalendarEvent] = Field(default_factory=list, description="A list of calendar events extracted from the image.")
    tasks: List[Task] = Field(default_factory=list, description="A list of tasks or to-do items extracted from the image.")

@tool(args_schema=ImageParseInput)
async def parse_image_for_tasks_and_events(image_url: str) -> str:
    """
    <tool_name>parse_image_for_tasks_and_events</tool_name>
    <description>
    Use this tool to analyze an image provided via a URL and extract any actionable tasks or calendar events it contains. This tool is ideal for interpreting images of whiteboards, screenshots, or photos of sticky notes. It can identify text and understand its context to create structured data.
    </description>
    <parameters>
        <parameter name="image_url">Required. The public URL of the image to be analyzed.</parameter>
    </parameters>
    <example>
    User: "Can you look at this picture and tell me what tasks are on the whiteboard? Here's the link: https://example.com/image.jpg"
    </example>
    """
    if not llm_manager_instance:
        return "Error: Parser tool not initialized with an LLM Manager."

    # Ensure the model in the manager supports vision, which gpt-4o-mini does.
    # The HumanMessage format with a list of content blocks is how we pass images.
    prompt_message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "You are an expert at analyzing images of whiteboards, sticky notes, and screenshots. "
                        "Your task is to carefully examine the following image and extract any calendar events "
                        "(with titles, dates, and times) and any to-do items or tasks (with titles). "
                        "Return the extracted information in a structured format. "
                        "If a date or time is relative (e.g., 'Tomorrow at 2pm'), calculate the absolute date and time. "
                        f"The current date is {datetime.now().isoformat()}.",
            },
            {
                "type": "image_url",
                "image_url": {"url": image_url},
            },
        ]
    )
    
    try:
        # Use a structured output call to get reliable, parsed data.
        structured_llm = llm_manager_instance.client.with_structured_output(ParsedImageContent)
        parsed_result = await structured_llm.ainvoke([prompt_message])

        response_parts = []
        if parsed_result.events:
            response_parts.append(f"I found {len(parsed_result.events)} event(s) in the image:")
            for event in parsed_result.events:
                response_parts.append(f"- Event: {event.title} at {event.start_time.strftime('%Y-%m-%d %I:%M %p')}")
        
        if parsed_result.tasks:
            response_parts.append(f"I found {len(parsed_result.tasks)} task(s) in the image:")
            for task in parsed_result.tasks:
                due_date_str = f" (due {task.due_date})" if task.due_date else ""
                response_parts.append(f"- Task: {task.title}{due_date_str}")

        if not response_parts:
            return "I analyzed the image but could not find any clear tasks or events to extract."

        response = "\\n".join(response_parts)
        response += "\\n\\nWould you like me to add these to your calendar and to-do list?"
        return response

    except Exception as e:
        return f"An error occurred while parsing the image: {e}"

# List of all parser-related tools
parser_tools_list = [parse_image_for_tasks_and_events]
