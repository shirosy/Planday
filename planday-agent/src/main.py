import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from core.agent_supervisor import AgentSupervisorSystem
from utils.cli_utils import fancy_print

async def main():
    """Main REPL loop for the PlanDay agent."""
    load_dotenv()
    config = {}  # Load your config here if needed
    
    # Create a thread pool executor that will be managed explicitly
    with ThreadPoolExecutor() as executor:
        supervisor = AgentSupervisorSystem(config, executor)
        await supervisor.setup()
        
        session_id = str(uuid.uuid4())

        fancy_print("🗓️ PlanDay Agent - Personal Scheduling Assistant", "bold cyan")
        fancy_print("Type 'quit' to exit, 'help' for examples.", "bold cyan")

        try:
            while True:
                try:
                    user_input = await asyncio.to_thread(input, "\n💬 You: ")
                    if user_input.lower() in ["quit", "exit"]:
                        break

                    fancy_print("🤖 PlanDay: Processing...", "bold green")
                    
                    result = await supervisor.process_request(user_input, session_id)
                    
                    if result["success"]:
                        fancy_print(f"🤖 PlanDay: {result['response']}", "bold green")
                    else:
                        fancy_print(f"🤖 PlanDay Error: {result['error']}", "bold red")
                        
                except (KeyboardInterrupt, asyncio.CancelledError):
                    break
                except Exception as e:
                    fancy_print(f"An unexpected error occurred: {e}", "bold red")
        finally:
            await supervisor.close()
            # The executor is automatically shut down by the 'with' statement

    fancy_print("\n👋 Exiting...", "bold cyan")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
