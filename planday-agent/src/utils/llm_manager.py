"""
Centralized LLM management for the PlanDay application.
"""
import os
from typing import Optional
import httpx
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = structlog.get_logger()

class LLMManager:
    """
    Handles the configuration and invocation of Large Language Models.
    """
    def __init__(self, config_or_manager: any = None, tools: Optional[list] = None):
        config = {}
        if isinstance(config_or_manager, LLMManager):
            # If an LLMManager instance is passed, extract its config
            config = {
                "openai_api_key": config_or_manager.api_key,
                "openai_api_base": config_or_manager.api_base,
                "model_name": config_or_manager.model_name,
                "temperature": config_or_manager.temperature,
            }
        elif isinstance(config_or_manager, dict):
            config = config_or_manager

        self.api_key = os.getenv("OPENAI_API_KEY", config.get("openai_api_key"))
        self.api_base = os.getenv("OPENAI_BASE_URL", config.get("openai_api_base", config.get("openai_base_url")))
        self.model_name = os.getenv("MODEL_NAME", config.get("model_name", "gpt-4o-mini"))
        self.temperature = config.get("temperature", 0.1)

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment or config.")

        logger.info(
            "Initializing LLMManager",
            model_name=self.model_name,
            api_base=self.api_base or "Default OpenAI",
        )

        sync_client = httpx.Client(trust_env=False)
        async_client = httpx.AsyncClient(trust_env=False)

        self.client = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key,
            base_url=self.api_base,
            http_client=sync_client,
            http_async_client=async_client,
            streaming=False,
        )

        if tools:
            self.client = self.client.bind_tools(tools)

    async def invoke(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Invokes the configured language model with a given prompt.
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_prompt))
        
        logger.info("Invoking LLM API...")
        response = await self.client.ainvoke(messages)
        logger.info("LLM API call successful.")
        
        return response.content

def get_llm_manager(config: dict = None) -> LLMManager:
    """Factory function to get an instance of the LLMManager."""
    return LLMManager(config)
