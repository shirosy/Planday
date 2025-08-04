"""Command Line Interface for PlanDay agent system."""

import asyncio
import uuid
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from src.main import PlanDayAgent

app = typer.Typer(help="🗓️ PlanDay - Personal Scheduling and Task Management Agent")
console = Console()


@app.command()
def interactive():
    """Start interactive chat mode with PlanDay agent."""
    asyncio.run(_interactive_mode())


@app.command()
def schedule(
    title: str = typer.Argument(..., help="Event title"),
    start_time: str = typer.Argument(..., help="Start time (e.g., '2024-01-15 14:00')"),
    end_time: str = typer.Argument(..., help="End time (e.g., '2024-01-15 15:00')"),
    description: str = typer.Option("", help="Event description"),
    location: str = typer.Option("", help="Event location"),
):
    """Schedule a calendar event."""
    asyncio.run(_schedule_event(title, start_time, end_time, description, location))


@app.command()
def task(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", help="Task description"),
    priority: str = typer.Option("medium", help="Priority (low/medium/high/urgent)"),
    due_date: str = typer.Option("", help="Due date (YYYY-MM-DD)"),
):
    """Create a new task."""
    asyncio.run(_create_task(title, description, priority, due_date))


@app.command()
def find_time(
    duration: int = typer.Argument(..., help="Duration in minutes"),
    date_range: str = typer.Option("this week", help="Date range (e.g., 'this week', 'today')"),
    preferences: str = typer.Option("", help="Scheduling preferences"),
):
    """Find available time slots."""
    asyncio.run(_find_time_slots(duration, date_range, preferences))


@app.command()
def recommend(
    context: str = typer.Option("", help="Context for recommendations"),
):
    """Get priority and scheduling recommendations."""
    asyncio.run(_get_recommendations(context))


@app.command()
def parse(
    content: str = typer.Argument(..., help="Content to parse"),
    content_type: str = typer.Option("text", help="Content type (text/email/image)"),
):
    """Parse content into tasks or events."""
    asyncio.run(_parse_content(content, content_type))


@app.command()
def status():
    """Show system status and information."""
    asyncio.run(_show_status())


async def _interactive_mode():
    """Interactive chat mode."""
    agent = PlanDayAgent()
    session_id = str(uuid.uuid4())
    
    console.print(Panel.fit(
        "[bold blue]🗓️ PlanDay Agent[/bold blue]\n"
        "[dim]Personal Scheduling and Task Management Assistant[/dim]\n\n"
        "Type 'help' for commands, 'quit' to exit",
        title="Welcome"
    ))
    
    # Show available commands
    console.print("\n[bold]Quick Commands:[/bold]")
    console.print("• Schedule: 'Schedule team meeting tomorrow 3-4pm'")
    console.print("• Tasks: 'Create task to finish report by Friday'")
    console.print("• Find time: 'Find 2 hours free time this week'")
    console.print("• Recommendations: 'What should I prioritize today?'")
    console.print("• Parse: 'Parse this email: [email content]'")
    
    while True:
        try:
            console.print()
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("👋 [bold blue]Goodbye![/bold blue]")
                break
            
            if user_input.lower() == 'help':
                _show_help()
                continue
            
            if user_input.lower() == 'clear':
                console.clear()
                continue
            
            if not user_input:
                continue
            
            # Show processing indicator
            with console.status("[bold blue]🤖 PlanDay is thinking...[/bold blue]"):
                result = await agent.chat(user_input, session_id)
            
            # Display response
            if result["success"]:
                response_text = Text(result["response"])
                console.print(Panel(response_text, title="🤖 PlanDay", border_style="blue"))
                
                # Show any events or tasks created
                if result.get("events"):
                    _display_events(result["events"])
                
                if result.get("tasks"):
                    _display_tasks(result["tasks"])
                
                if result.get("recommendations"):
                    _display_recommendations(result["recommendations"])
            
            else:
                console.print(f"[bold red]❌ Error:[/bold red] {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            console.print("\n👋 [bold blue]Goodbye![/bold blue]")
            break
        except Exception as e:
            console.print(f"[bold red]❌ Unexpected error:[/bold red] {e}")


async def _schedule_event(title: str, start_time: str, end_time: str, description: str, location: str):
    """Schedule an event using direct API."""
    agent = PlanDayAgent()
    
    with console.status("[bold blue]📅 Scheduling event...[/bold blue]"):
        result = await agent.schedule_event(title, start_time, end_time, description, location)
    
    if result["success"]:
        console.print(f"[bold green]✅ Success:[/bold green] {result['response']}")
        if result.get("events"):
            _display_events(result["events"])
    else:
        console.print(f"[bold red]❌ Error:[/bold red] {result.get('error', 'Failed to schedule event')}")


async def _create_task(title: str, description: str, priority: str, due_date: str):
    """Create a task using direct API."""
    agent = PlanDayAgent()
    
    with console.status("[bold blue]📝 Creating task...[/bold blue]"):
        result = await agent.create_task(title, description, priority, due_date)
    
    if result["success"]:
        console.print(f"[bold green]✅ Success:[/bold green] {result['response']}")
        if result.get("tasks"):
            _display_tasks(result["tasks"])
    else:
        console.print(f"[bold red]❌ Error:[/bold red] {result.get('error', 'Failed to create task')}")


async def _find_time_slots(duration: int, date_range: str, preferences: str):
    """Find available time slots."""
    agent = PlanDayAgent()
    
    with console.status("[bold blue]🔍 Finding available time slots...[/bold blue]"):
        result = await agent.find_time_slots(duration, date_range, preferences)
    
    if result["success"]:
        console.print(f"[bold green]✅ Success:[/bold green] {result['response']}")
        # Would display time slots if available in result
    else:
        console.print(f"[bold red]❌ Error:[/bold red] {result.get('error', 'Failed to find time slots')}")


async def _get_recommendations(context: str):
    """Get recommendations."""
    agent = PlanDayAgent()
    
    with console.status("[bold blue]💡 Generating recommendations...[/bold blue]"):
        result = await agent.get_recommendations(context)
    
    if result["success"]:
        console.print(f"[bold green]✅ Success:[/bold green] {result['response']}")
        if result.get("recommendations"):
            _display_recommendations(result["recommendations"])
    else:
        console.print(f"[bold red]❌ Error:[/bold red] {result.get('error', 'Failed to generate recommendations')}")


async def _parse_content(content: str, content_type: str):
    """Parse content."""
    agent = PlanDayAgent()
    
    with console.status("[bold blue]🔍 Parsing content...[/bold blue]"):
        result = await agent.parse_content(content, content_type)
    
    if result["success"]:
        console.print(f"[bold green]✅ Success:[/bold green] {result['response']}")
        
        if result.get("events"):
            console.print("[bold]📅 Extracted Events:[/bold]")
            _display_events(result["events"])
        
        if result.get("tasks"):
            console.print("[bold]📝 Extracted Tasks:[/bold]")
            _display_tasks(result["tasks"])
    else:
        console.print(f"[bold red]❌ Error:[/bold red] {result.get('error', 'Failed to parse content')}")


async def _show_status():
    """Show system status."""
    agent = PlanDayAgent()
    info = agent.get_system_info()
    
    console.print(Panel.fit(
        f"[bold]Version:[/bold] {info['version']}\n"
        f"[bold]Active Sessions:[/bold] {info['active_sessions']}\n"
        f"[bold]Features:[/bold]\n"
        f"  • Image Parsing: {'✅' if info['features']['image_parsing'] else '❌'}\n"
        f"  • Email Parsing: {'✅' if info['features']['email_parsing'] else '❌'}\n"
        f"  • Smart Recommendations: {'✅' if info['features']['smart_recommendations'] else '❌'}",
        title="📊 PlanDay Status"
    ))


def _show_help():
    """Show help information."""
    console.print(Panel.fit(
        "[bold]Available Commands:[/bold]\n\n"
        "[bold cyan]Scheduling:[/bold cyan]\n"
        "• 'Schedule [event] [time]' - Create calendar events\n"
        "• 'Book meeting tomorrow 3-4pm' - Schedule meetings\n\n"
        "[bold cyan]Tasks:[/bold cyan]\n"
        "• 'Create task [description]' - Add to-do items\n"
        "• 'Remind me to [action]' - Set reminders\n\n"
        "[bold cyan]Time Management:[/bold cyan]\n"
        "• 'Find [duration] free time' - Locate available slots\n"
        "• 'What should I prioritize?' - Get recommendations\n\n"
        "[bold cyan]Content Parsing:[/bold cyan]\n"
        "• 'Parse this email: [content]' - Extract events/tasks\n"
        "• 'Parse image: [description]' - Analyze images\n\n"
        "[bold cyan]Utility:[/bold cyan]\n"
        "• 'help' - Show this help\n"
        "• 'clear' - Clear screen\n"
        "• 'quit' / 'exit' - Exit PlanDay",
        title="💡 Help"
    ))


def _display_events(events: list):
    """Display events in a formatted table."""
    if not events:
        return
    
    table = Table(title="📅 Calendar Events")
    table.add_column("Title", style="cyan")
    table.add_column("Start Time", style="green")
    table.add_column("End Time", style="green")
    table.add_column("Location", style="yellow")
    
    for event in events:
        table.add_row(
            event.get("title", "Untitled"),
            event.get("start_time", ""),
            event.get("end_time", ""),
            event.get("location", "")
        )
    
    console.print(table)


def _display_tasks(tasks: list):
    """Display tasks in a formatted table."""
    if not tasks:
        return
    
    table = Table(title="📝 Tasks")
    table.add_column("Title", style="cyan")
    table.add_column("Priority", style="red")
    table.add_column("Status", style="green")
    table.add_column("Due Date", style="yellow")
    
    for task in tasks:
        priority_color = {
            "urgent": "[bold red]URGENT[/bold red]",
            "high": "[red]HIGH[/red]",
            "medium": "[yellow]MEDIUM[/yellow]",
            "low": "[green]LOW[/green]"
        }.get(task.get("priority", "medium"), task.get("priority", "medium"))
        
        table.add_row(
            task.get("title", "Untitled"),
            priority_color,
            task.get("status", "pending"),
            task.get("due_date", "")
        )
    
    console.print(table)


def _display_recommendations(recommendations: list):
    """Display recommendations."""
    if not recommendations:
        return
    
    console.print("\n[bold]💡 Recommendations:[/bold]")
    for i, rec in enumerate(recommendations, 1):
        console.print(f"{i}. {rec.get('reasoning', 'No reasoning provided')}")


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()