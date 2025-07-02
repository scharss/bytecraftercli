import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
import re
import html

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from bytecrafter import agent, tools, ui
from bytecrafter.memory import init_database, ConversationManager, ContextManager, LearningEngine

app = typer.Typer()
console = Console()

# Gestores de memoria persistente
conversation_manager = ConversationManager()
context_manager = ContextManager()
learning_engine = LearningEngine()

# Fallback: In-memory history for when memory is disabled
conversation_history: List[Dict] = []


def clean_tool_result_for_gemini(content: str) -> str:
    """Limpia mensajes de tool_result para que Gemini no se confunda con el XML"""
    if "<tool_result>" in content and "</tool_result>" in content:
        try:
            # Extraer tool_name y result del XML
            tool_name_match = re.search(r'<tool_name>(.*?)</tool_name>', content)
            result_match = re.search(r'<result>(.*?)</result>', content, re.DOTALL)
            error_match = re.search(r'<error>(.*?)</error>', content, re.DOTALL)
            
            if tool_name_match:
                tool_name = tool_name_match.group(1)
                
                if result_match:
                    result = result_match.group(1)
                    return f"Tool: {tool_name}\nResult: {result}"
                elif error_match:
                    error = error_match.group(1)
                    return f"Tool: {tool_name}\nError: {error}"
            
            # Si no se puede parsear, devolver el contenido original
            return content
        except:
            return content
    
    # Si no es tool_result, devolver tal como está
    return content

def clean_history_for_gemini(history: List[Dict]) -> List[Dict]:
    """Limpia el historial completo para envío a Gemini"""
    cleaned_history = []
    for msg in history:
        cleaned_msg = msg.copy()
        # Limpiar cada parte del mensaje
        if "parts" in cleaned_msg:
            cleaned_parts = []
            for part in cleaned_msg["parts"]:
                if "text" in part:
                    cleaned_text = clean_tool_result_for_gemini(part["text"])
                    cleaned_parts.append({"text": cleaned_text})
                else:
                    cleaned_parts.append(part)
            cleaned_msg["parts"] = cleaned_parts
        cleaned_history.append(cleaned_msg)
    return cleaned_history

def parse_agent_response(text: str) -> Optional[Tuple[str, str, Dict[str, str]]]:
    """
    Parses the agent's XML-based response to extract thinking, tool name, and parameters.
    """
    try:
        # The response may contain markdown formatting, so we clean it first
        cleaned_text = text.replace("```xml", "").replace("```", "").strip()
        
        # Sanitize special characters (e.g., & < >) inside tags that typically hold free-form text
        for tag in ["command", "result", "question", "answer"]:
            cleaned_text = re.sub(
                rf"<{tag}>(.*?)</{tag}>",
                lambda m: f"<{tag}>{html.escape(m.group(1))}</{tag}>",
                cleaned_text,
                flags=re.DOTALL,
            )

        # Wrap the text in a root tag to make it valid XML
        xml_text = f"<root>{cleaned_text}</root>"
        root = ET.fromstring(xml_text)

        thinking_element = root.find("thinking")
        thinking = thinking_element.text.strip() if thinking_element is not None and thinking_element.text else ""

        tool_element = None
        for child in root:
            if child.tag not in ["thinking", "root", "tool_result"]:
                tool_element = child
                break
        
        if tool_element is None:
            # This could be a pure thinking response without a tool
            return thinking, None, {}

        tool_name = tool_element.tag
        parameters = {child.tag: child.text.strip() if child.text else "" for child in tool_element}

        return thinking, tool_name, parameters

    except ET.ParseError as e:
        console.print(f"[bold red]XML Parse Error: Failed to parse agent response.[/bold red]\nRaw Response:\n{text}")
        return None
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during parsing: {e}[/bold red]")
        return None


def run_tool_loop(model: str):
    """
    The main autonomous loop for the agent.
    It continuously executes tools until the task is completed, requires user input, or an error occurs.
    """
    while True:
        console.print("\n[bold]Thinking...[/bold]")
        
        # Usar memoria persistente o temporal según disponibilidad
        if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
            # Obtener historial desde base de datos (ya limpiado)
            history = conversation_manager.get_conversation_history()
            if not history:
                history = clean_history_for_gemini(conversation_history)  # Limpiar fallback
        else:
            history = clean_history_for_gemini(conversation_history)
        
        response = agent.get_llm_response(history, model or None)
        
        if "error" in response:
            console.print(Panel(f"[bold red]Error:[/bold red] {response['error']}", title="Error", border_style="red"))
            break # Exit the loop on API error

        # Convert response to plain text depending on provider
        if isinstance(response, dict) and "content" in response:
            agent_response_text = response["content"]
        else:
            console.print("[bold red]Unrecognized response format from LLM provider[/bold red]")
            break
        
        # Guardar respuesta del agente en memoria persistente
        conversation_manager.save_message("model", agent_response_text)
        conversation_history.append({"role": "model", "parts": [{"text": agent_response_text}]})

        parsed_response = parse_agent_response(agent_response_text)
        if not parsed_response:
            break # Exit loop on parsing error

        thinking, tool_name, tool_args = parsed_response

        if not tool_name:
             ui.display_thinking(thinking)
             console.print("[bold yellow]Agent paused. What's the next step?[/bold yellow]")
             break

        if tool_name == "ask_followup_question":
            ui.display_question(thinking, tool_args.get("question", "No question found."))
            break # Exit loop to get user input

        if tool_name == "attempt_completion":
            ui.display_completion(thinking, tool_args.get("result", "No result found."))
            # Completar conversación en memoria persistente
            completion_summary = tool_args.get("result", "Tarea completada")[:200]
            conversation_manager.complete_conversation(completion_summary)
            return "COMPLETED" # Signal completion to the main function

        # For all other tools, execute them without asking for confirmation
        console.print(f"\n[bold cyan]🤖 Bytecrafter is running [bold blue]{tool_name}[/bold blue]...[/bold cyan]")
        ui.display_thinking(thinking)
        
        try:
            tool_function = getattr(tools, tool_name)
            tool_result = tool_function(**tool_args)

            console.print(Panel(tool_result, title=f"Result from [bold blue]{tool_name}[/bold blue]", border_style="green"))

            tool_result_text = f"<tool_result><tool_name>{tool_name}</tool_name><result>{tool_result}</result></tool_result>"
            
            # Guardar resultado de herramienta en memoria persistente
            conversation_manager.save_message("user", tool_result_text, tool_name, tool_args, tool_result)
            conversation_history.append({"role": "user", "parts": [{"text": tool_result_text}]})
            
            # Aprender de la herramienta ejecutada (solo patrones exitosos)
            if tool_name in ["read_file", "list_files"]:
                learning_engine.learn_user_pattern("tool_usage", {
                    "key": tool_name,
                    "success": True,
                    "context": tool_args
                })
        
        except Exception as e:
            error_message = f"Error executing tool {tool_name}: {e}"
            console.print(f"[bold red]{error_message}[/bold red]")
            tool_error_text = f"<tool_result><tool_name>{tool_name}</tool_name><error>{error_message}</error></tool_result>"
            
            # Guardar error en memoria persistente
            conversation_manager.save_message("user", tool_error_text, tool_name, tool_args, error_message)
            conversation_history.append({"role": "user", "parts": [{"text": tool_error_text}]})
            
            # Aprender del error
            learning_engine.learn_error_solution(
                error_type=type(e).__name__,
                error_message=str(e),
                solution="Tool execution failed - review parameters",
                context={"tool_name": tool_name, "tool_args": tool_args}
            )
            
            break # Exit loop on tool error

@app.command()
def main(
    model: str = typer.Option(
        lambda: os.getenv("DEFAULT_MODEL", None),
        "--model",
        "-m",
        help="Optional model override. If omitted, provider default is used.",
    )
):
    """
    Start an interactive session with the Bytecrafter agent, powered by Gemini.
    """
    console.print("[bold green]Welcome to Bytecrafter CLI (Autonomous Edition)! 🤖[/bold green]")
    
    # Inicializar sistema de memoria
    memory_enabled = init_database()
    if memory_enabled:
        console.print("🧠 [bold cyan]Sistema de memoria persistente activado![/bold cyan]")
        console.print("   Bytecrafter recordará nuestras conversaciones anteriores.")
    else:
        console.print("⚠️  [yellow]Sistema de memoria desactivado - usando memoria temporal[/yellow]")
    
    console.print("Your AI assistant for coding tasks. Type 'exit' or 'quit' to end.")

    while True:
        try:
            # 1. Get initial user input
            user_input = console.input("[bold yellow]You: [/bold yellow]")
            
            if user_input.lower() in ["exit", "quit"]:
                console.print("[bold]Goodbye![/bold]")
                break
            
            # Agregar contexto de memoria a la consulta del usuario
            if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
                # Buscar contexto relevante en conversaciones anteriores
                conversation_context = conversation_manager.get_context_for_query(user_input)
                
                # Buscar contexto relevante en proyectos
                project_context = context_manager.get_context_for_query(user_input)
                
                # Buscar contexto relevante en aprendizajes
                learning_context = learning_engine.get_context_for_query(user_input)
                
                # Construir mensaje enriquecido con contexto
                enriched_input = user_input
                context_parts = []
                
                if conversation_context:
                    context_parts.append(conversation_context)
                if project_context:
                    context_parts.append(project_context)
                if learning_context:
                    context_parts.append(learning_context)
                
                if context_parts:
                    enriched_input = f"{user_input}\n\n{chr(10).join(context_parts)}"
                    console.print("[dim]🧠 Consultando memoria previa...[/dim]")
                
                # Guardar mensaje del usuario en memoria persistente
                conversation_manager.save_message("user", enriched_input)
                conversation_history.append({"role": "user", "parts": [{"text": enriched_input}]})
            else:
                conversation_history.append({"role": "user", "parts": [{"text": user_input}]})

            # 2. Get the first plan from the agent
            console.print("\n[bold]Thinking...[/bold]")
            
            # Usar memoria persistente o temporal según disponibilidad
            if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
                history = conversation_manager.get_conversation_history()
                if not history:
                    history = clean_history_for_gemini(conversation_history)
            else:
                history = clean_history_for_gemini(conversation_history)
                
            response = agent.get_llm_response(history, model or None)

            if "error" in response:
                console.print(Panel(f"[bold red]Error:[/bold red] {response['error']}", title="Error", border_style="red"))
                conversation_history.pop()
                continue
            
            # Convert response to plain text depending on provider
            if isinstance(response, dict) and "content" in response:
                agent_response_text = response["content"]
            else:
                console.print("[bold red]Unrecognized response format from LLM provider[/bold red]")
                break
            
            # Guardar respuesta del agente en memoria persistente
            if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
                conversation_manager.save_message("model", agent_response_text)
                
            conversation_history.append({"role": "model", "parts": [{"text": agent_response_text}]})

            parsed_response = parse_agent_response(agent_response_text)
            if not parsed_response:
                continue

            thinking, tool_name, tool_args = parsed_response

            if not tool_name:
                ui.display_thinking(thinking)
                continue

            # 3. Display the first step and get confirmation to start the loop
            if ui.display_tool_call(thinking, tool_name, tool_args):
                # 4. Execute the first step
                try:
                    tool_function = getattr(tools, tool_name)
                    tool_result = tool_function(**tool_args)
                    console.print(Panel(tool_result, title=f"Result from [bold blue]{tool_name}[/bold blue]", border_style="green"))
                    
                    tool_result_text = f"<tool_result><tool_name>{tool_name}</tool_name><result>{tool_result}</result></tool_result>"
                    
                    # Guardar resultado de herramienta en memoria persistente
                    if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
                        conversation_manager.save_message("user", tool_result_text, tool_name, tool_args, tool_result)
                        
                    conversation_history.append({"role": "user", "parts": [{"text": tool_result_text}]})

                    # 5. Start the autonomous loop
                    loop_status = run_tool_loop(model)
                    if loop_status == "COMPLETED":
                        console.print("[bold green]Agent finished the task. Ready for a new one.[/bold green]")
                        
                        # En lugar de borrar completamente, iniciar nueva conversación
                        if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
                            # La conversación ya se marcó como completada en run_tool_loop
                            console.print("[dim]💾 Conversación guardada en memoria persistente[/dim]")
                        else:
                            conversation_history.clear() # Solo limpiar si no hay memoria persistente

                except Exception as e:
                    console.print(f"[bold red]Error executing initial tool {tool_name}: {e}[/bold red]")
                    
                    # Aprender del error
                    if os.getenv("ENABLE_MEMORY", "true").lower() == "true":
                        learning_engine.learn_error_solution(
                            error_type=type(e).__name__,
                            error_message=str(e),
                            solution="Initial tool execution failed",
                            context={"tool_name": tool_name, "tool_args": tool_args}
                        )
            else:
                console.print("[bold red]Execution cancelled by user.[/bold red]")
                
                # No borrar historial cuando se cancela - mantener contexto
                if os.getenv("ENABLE_MEMORY", "true").lower() != "true":
                    conversation_history.clear()
                
        except KeyboardInterrupt:
            console.print("\n[bold]Goodbye![/bold]")
            break
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred in main loop: {e}[/bold red]")
            if conversation_history:
                conversation_history.pop()


if __name__ == "__main__":
    app() 