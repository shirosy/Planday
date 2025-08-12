"""Command-line interface utilities for PlanDay."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Initialize a Rich console for consistent output styling
console = Console()

def fancy_print(text: str, style: str = "", title: str = None):
    """
    Prints text to the console with rich formatting.

    Args:
        text (str): The text to print.
        style (str): A Rich style string (e.g., "bold green").
        title (str, optional): An optional title for a panel.
    """
    if title:
        console.print(Panel(Markdown(text), title=title, border_style="cyan", expand=False))
    else:
        console.print(Markdown(text), style=style)
