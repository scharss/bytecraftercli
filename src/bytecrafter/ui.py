from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

def display_thinking(thinking: str):
    """Displays the agent's thinking process."""
    if thinking:
        console.print(Panel(Markdown(thinking), title="[bold yellow]🤔 Thinking[/bold yellow]", border_style="yellow"))

def display_tool_call(thinking: str, tool_name: str, parameters: dict) -> bool:
    """
    Displays the agent's plan (thinking, tool name, and parameters) and asks for confirmation.
    """
    console.print("\n[bold cyan]🤖 Bytecrafter proposes a plan...[/bold cyan]")
    display_thinking(thinking)

    table = Table(title="[bold]Execution Plan[/bold]", show_header=True, header_style="bold magenta")
    table.add_column("Tool", style="dim", width=20)
    table.add_column("Parameters")

    param_str = "\n".join(f"[bold]{k}:[/bold] '{v}'" for k, v in parameters.items())
    
    table.add_row(f"[bold blue]{tool_name}[/bold blue]", param_str)
    
    console.print(table)

    try:
        choice = Prompt.ask("\n[bold]Do you want to execute this plan?", choices=["y", "n"], default="y")
        return choice.lower() == "y"
    except Exception:
        return False

def display_question(thinking: str, question: str):
    """Displays a question from the agent to the user."""
    console.print("\n[bold cyan]🤖 Bytecrafter has a question...[/bold cyan]")
    display_thinking(thinking)
    console.print(Panel(Markdown(question), title="[bold magenta]❓ Question[/bold magenta]", border_style="magenta"))

def display_completion(thinking: str, result: str):
    """Displays the final result of the task."""
    console.print("\n[bold green]✅ Task Completed[/bold green]")
    display_thinking(thinking)
    console.print(Panel(Markdown(result), title="[bold green]🎉 Result[/bold green]", border_style="green")) 