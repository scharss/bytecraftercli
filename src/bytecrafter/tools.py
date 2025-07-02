import subprocess
import shlex
import google.generativeai as genai
import os
import chardet
import mimetypes
from pathlib import Path
from duckduckgo_search import DDGS
import json

# File handling utilities
def detect_file_encoding(file_path: str) -> str:
    """Detects file encoding using chardet with enhanced UTF-16 support."""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(32768)  # Read more data for better detection
            if not raw_data:
                return 'utf-8'  # Default for empty files
            
            # Check for BOM first
            if raw_data.startswith(b'\xff\xfe'):
                return 'utf-16le'
            elif raw_data.startswith(b'\xfe\xff'):
                return 'utf-16be'
            elif raw_data.startswith(b'\xff\xfe\x00\x00'):
                return 'utf-32le'
            elif raw_data.startswith(b'\x00\x00\xfe\xff'):
                return 'utf-32be'
            elif raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            
            # Use chardet for detection
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            # Handle chardet's UTF-16 detection quirks
            if encoding and 'utf-16' in encoding.lower():
                # Verify UTF-16 by trying to decode
                try:
                    raw_data.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    # Try both UTF-16 variants
                    for utf16_variant in ['utf-16le', 'utf-16be']:
                        try:
                            raw_data.decode(utf16_variant)
                            return utf16_variant
                        except UnicodeDecodeError:
                            continue
            
            # If confidence is good and encoding is valid, use it
            if confidence > 0.7 and encoding:
                try:
                    raw_data.decode(encoding)
                    return encoding
                except (UnicodeDecodeError, LookupError):
                    pass
            
            # Fallback to trying common encodings
            fallback_encodings = ['utf-8', 'utf-16le', 'utf-16be', 'latin1', 'cp1252', 'iso-8859-1']
            for fallback_encoding in fallback_encodings:
                try:
                    raw_data.decode(fallback_encoding)
                    return fallback_encoding
                except (UnicodeDecodeError, LookupError):
                    continue
            
            return 'utf-8'  # Ultimate fallback
    except Exception:
        return 'utf-8'

def is_binary_file(file_path: str) -> bool:
    """Checks if a file is binary using intelligent detection."""
    try:
        # First check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return not mime_type.startswith('text/')
        
        # Use chardet to detect if it's text in any encoding (including UTF-16)
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)  # Read more data for better detection
            if not chunk:
                return False  # Empty file is text
            
            # Try to detect encoding first
            result = chardet.detect(chunk)
            encoding = result.get('encoding', '').lower()
            confidence = result.get('confidence', 0)
            
            # If chardet detects a text encoding with decent confidence, it's text
            if encoding and confidence > 0.5:
                # Known text encodings
                text_encodings = ['utf-8', 'utf-16', 'utf-16le', 'utf-16be', 'utf-32', 
                                'ascii', 'latin1', 'cp1252', 'iso-8859-1']
                if any(enc in encoding for enc in text_encodings):
                    return False  # It's text
            
            # Fallback: check for null bytes, but exclude UTF-16 patterns
            null_count = chunk.count(b'\x00')
            total_bytes = len(chunk)
            
            if null_count == 0:
                return False  # No nulls = likely text
            
            # If roughly half the bytes are null, might be UTF-16
            if total_bytes > 0 and 0.3 <= (null_count / total_bytes) <= 0.7:
                # Check for UTF-16 BOM or patterns
                if chunk.startswith(b'\xff\xfe') or chunk.startswith(b'\xfe\xff'):
                    return False  # UTF-16 with BOM = text
                
                # Check for UTF-16LE pattern (ASCII chars followed by null)
                ascii_null_pattern = 0
                for i in range(0, min(100, len(chunk) - 1), 2):
                    if 32 <= chunk[i] <= 126 and chunk[i + 1] == 0:  # ASCII + null
                        ascii_null_pattern += 1
                
                if ascii_null_pattern > 10:  # Strong UTF-16LE pattern
                    return False  # It's UTF-16 text
            
            # High null density = likely binary
            if null_count / total_bytes > 0.3:
                return True
                
            return False  # Default to text
            
    except Exception:
        return False

def get_file_info(file_path: str) -> dict:
    """Gets comprehensive file information."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"exists": False, "error": "File does not exist"}
        
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(file_path)
        is_binary = is_binary_file(file_path)
        encoding = None if is_binary else detect_file_encoding(file_path)
        
        return {
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size": stat.st_size,
            "mime_type": mime_type,
            "is_binary": is_binary,
            "encoding": encoding,
            "readable": os.access(file_path, os.R_OK),
            "writable": os.access(file_path, os.W_OK)
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}

def safe_path_validation(path: str) -> tuple[bool, str]:
    """Validates if a path is safe and accessible."""
    try:
        # Convert to absolute path for validation
        abs_path = os.path.abspath(path)
        
        # Check if path exists
        if not os.path.exists(abs_path):
            return False, f"Path '{path}' does not exist"
        
        # Check if path is accessible
        if not os.access(abs_path, os.R_OK):
            return False, f"Path '{path}' is not readable"
        
        return True, "Path is valid and accessible"
    except Exception as e:
        return False, f"Error validating path '{path}': {str(e)}"

# Helper to create function declarations
def make_tool(name: str, description: str, properties: dict, required: list):
    return genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name=name,
                description=description,
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties=properties,
                    required=required
                )
            )
        ]
    )

# Function declarations for Gemini
read_file_declaration = genai.protos.FunctionDeclaration(
    name="read_file",
    description="Reads a file and returns its content.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "file_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="The path to the file.")
        },
        required=["file_path"]
    )
)

create_file_declaration = genai.protos.FunctionDeclaration(
    name="create_file",
    description="Creates or overwrites a file with the given content.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "file_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="The path for the new file."),
            "content": genai.protos.Schema(type=genai.protos.Type.STRING, description="The content to write to the file.")
        },
        required=["file_path", "content"]
    )
)

edit_file_declaration = genai.protos.FunctionDeclaration(
    name="edit_file",
    description="A specific function for editing, overwriting an existing file with new content.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "file_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="The path of the file to edit."),
            "new_content": genai.protos.Schema(type=genai.protos.Type.STRING, description="The new content to write.")
        },
        required=["file_path", "new_content"]
    )
)

execute_command_declaration = genai.protos.FunctionDeclaration(
    name="execute_command",
    description="Executes a shell command and returns its output (stdout/stderr).",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "command": genai.protos.Schema(type=genai.protos.Type.STRING, description="The shell command to execute.")
        },
        required=["command"]
    )
)

answer_user_declaration = genai.protos.FunctionDeclaration(
    name="answer_user",
    description="A tool for when the agent just needs to talk to the user to answer a question or ask for clarification.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "response": genai.protos.Schema(type=genai.protos.Type.STRING, description="The response to give to the user.")
        },
        required=["response"]
    )
)

list_files_declaration = genai.protos.FunctionDeclaration(
    name="list_files",
    description="Lists all files and directories in a given path, recursively. Essential for exploring the project structure.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "path": genai.protos.Schema(type=genai.protos.Type.STRING, description="The path to the directory to list. Defaults to the current directory '.'")
        },
        required=["path"]
    )
)

web_search_declaration = genai.protos.FunctionDeclaration(
    name="web_search",
    description="Performs a web search using DuckDuckGo to get up-to-date information, answer questions, or find code examples.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "query": genai.protos.Schema(type=genai.protos.Type.STRING, description="The search query.")
        },
        required=["query"]
    )
)

inspect_file_declaration = genai.protos.FunctionDeclaration(
    name="inspect_file",
    description="Inspects a file and returns detailed information about it without reading the full content. Useful for binary files, large files, or when you need to know file properties.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "file_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="The path to the file to inspect.")
        },
        required=["file_path"]
    )
)

safe_execute_declaration = genai.protos.FunctionDeclaration(
    name="safe_execute",
    description="Executes a command with enhanced error handling and safety checks. Provides better feedback for common issues.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "command": genai.protos.Schema(type=genai.protos.Type.STRING, description="The shell command to execute safely."),
            "working_dir": genai.protos.Schema(type=genai.protos.Type.STRING, description="Optional working directory for the command.")
        },
        required=["command"]
    )
)


# === Path normalization helpers ===
# Detect the project root ONCE at import time. By default we assume the
# current working directory (where the CLI is launched) is the project
# root. This can be overridden via the PROJECT_ROOT environment variable
# if necessary.
PROJECT_ROOT: str = os.getenv("PROJECT_ROOT", os.getcwd())


def _normalize_path(path: str) -> str:
    """Ensure paths are **always** inside the project root.

    1. Absolute paths (starting with os.sep) are treated as *relative* to the
       project root – this prevents the agent from accidentally writing to
       arbitrary locations like "/etc".
    2. Relative paths are joined to the project root.

    The returned path is an *absolute* path guaranteed to live inside
    PROJECT_ROOT.
    """
    # Strip root from absolute paths that don't already reside in PROJECT_ROOT
    if os.path.isabs(path):
        # If already inside the project root, keep it
        if os.path.commonpath([path, PROJECT_ROOT]) == PROJECT_ROOT:
            abs_path = path
        else:
            # Treat leading '/' as "relative to project root"
            rel_path = path.lstrip(os.sep)
            abs_path = os.path.join(PROJECT_ROOT, rel_path)
    else:
        # Already relative – anchor it to the project root
        abs_path = os.path.join(PROJECT_ROOT, path)

    # Normalise (eliminate .. etc.)
    abs_path = os.path.normpath(abs_path)

    # Final safety-check: make sure the resulting path is *inside* the project root
    if os.path.commonpath([abs_path, PROJECT_ROOT]) != PROJECT_ROOT:
        raise ValueError(f"Refusing to access path outside project root: {path}")

    return abs_path


# Tool implementations (the actual Python functions)
def read_file(path: str) -> str:
    """Reads a file and returns its content with intelligent encoding detection."""
    try:
        # First, validate the path
        is_valid, validation_message = safe_path_validation(path)
        if not is_valid:
            return f"Error: {validation_message}"
        
        # Get file information
        file_info = get_file_info(path)
        if not file_info.get("exists", False):
            return f"Error: {file_info.get('error', 'File does not exist')}"
        
        if not file_info.get("is_file", False):
            return f"Error: '{path}' is not a file (it might be a directory)"
        
        if not file_info.get("readable", False):
            return f"Error: '{path}' is not readable (permission denied)"
        
        # Handle binary files
        if file_info.get("is_binary", False):
            mime_type = file_info.get("mime_type", "unknown")
            size = file_info.get("size", 0)
            
            return (f"🚫 Cannot read binary file '{path}'\n"
                   f"📄 File type: {mime_type}\n"
                   f"📏 Size: {size:,} bytes\n"
                   f"💡 Suggestion: Use appropriate tools for this file type, or use 'execute_command' with tools like 'file', 'xxd', or 'strings' for binary analysis.")
        
        # Read text file with detected encoding
        encoding = file_info.get("encoding", "utf-8")
        try:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            
            # Add helpful information for large files
            lines = content.count('\n') + 1
            chars = len(content)
            
            if chars > 50000:  # Large file warning
                return (f"📄 File '{path}' (Encoding: {encoding})\n"
                       f"📏 Size: {chars:,} characters, {lines:,} lines\n"
                       f"⚠️  This is a large file. Consider using grep or other tools for specific searches.\n\n"
                       f"{content}")
            else:
                return (f"📄 File '{path}' (Encoding: {encoding})\n"
                       f"📏 Size: {chars:,} characters, {lines:,} lines\n\n"
                       f"{content}")
                
        except UnicodeDecodeError as e:
            # Try alternative encodings as fallback
            for fallback_encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(path, "r", encoding=fallback_encoding) as f:
                        content = f.read()
                    return (f"📄 File '{path}' (Fallback encoding: {fallback_encoding})\n"
                           f"⚠️  Original encoding detection failed, using fallback\n\n"
                           f"{content}")
                except UnicodeDecodeError:
                    continue
            
            return f"Error: Could not decode file '{path}' with any supported encoding. Original error: {e}"
    
    except Exception as e:
        return f"Error reading file '{path}': {e}"

def write_to_file(path: str, content: str) -> str:
    """Creates/overwrites a file with the given content, always anchoring the
    path inside the project root and creating parent directories if needed."""
    try:
        # Normalise path so it always points inside PROJECT_ROOT
        abs_path = _normalize_path(path)

        # Ensure the parent directory exists before creating the file
        dir_path = os.path.dirname(abs_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{abs_path}' written successfully."
    except Exception as e:
        return f"Error writing to file: {e}"

def edit_file(file_path: str, new_content: str) -> str:
    """A specific function for editing, essentially the same as create_file.
    Uses the same normalised path handling as write_to_file."""
    return write_to_file(file_path, new_content)

def execute_command(command: str) -> str:
    """Executes a shell command and returns its output."""
    try:
        if not command:
            return "Error: Empty command."
        
        # For security, split the command into a list of arguments
        split_command = shlex.split(command)
        
        result = subprocess.run(
            split_command,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit codes
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
            
        if not output:
            return "Command executed with no output."
            
        return output

    except FileNotFoundError:
        return f"Error: Command not found: {shlex.split(command)[0]}"
    except Exception as e:
        return f"Error executing command: {e}"

def ask_followup_question(question: str, options: str = None) -> str:
    """
    Herramienta mejorada para hacer preguntas de seguimiento al usuario.
    Similar a la funcionalidad de Cline para preguntas interactivas.
    
    Args:
        question: La pregunta a hacer al usuario
        options: Opciones separadas por comas (ej: "Sí,No,Tal vez")
    """
    # Esta función se maneja especialmente en main.py para mostrar la pregunta
    output = f"🤔 Pregunta: {question}"
    
    if options:
        option_list = [opt.strip() for opt in options.split(",")]
        output += f"\n\n📋 Opciones disponibles:"
        for i, option in enumerate(option_list, 1):
            output += f"\n  {i}. {option}"
        output += f"\n\n💡 Responde con el número de opción o escribe tu respuesta personalizada."
    
    return output

def list_files(path: str = ".") -> str:
    """Lists files and directories with enhanced information and better error handling."""
    try:
        # Validate path first
        is_valid, validation_message = safe_path_validation(path)
        if not is_valid:
            return f"Error: {validation_message}"
        
        # Normalize path
        abs_path = os.path.abspath(path)
        
        if not os.path.isdir(abs_path):
            # If it's a file, show file info instead
            if os.path.isfile(abs_path):
                file_info = get_file_info(abs_path)
                size = file_info.get("size", 0)
                mime_type = file_info.get("mime_type", "unknown")
                is_binary = file_info.get("is_binary", False)
                encoding = file_info.get("encoding", "N/A") if not is_binary else "binary"
                
                return (f"📄 '{path}' is a file, not a directory\n"
                       f"📏 Size: {size:,} bytes\n"
                       f"📄 Type: {mime_type}\n"
                       f"🔤 Encoding: {encoding}")
            else:
                return f"Error: '{path}' is not a valid directory or file."
        
        # Count items for summary
        total_files = 0
        total_dirs = 0
        total_size = 0
        
        output = f"📂 Contents of '{path}' (absolute: {abs_path}):\n\n"
        
        # List immediate contents first (non-recursive overview)
        try:
            immediate_items = sorted(os.listdir(abs_path))
            if not immediate_items:
                output += "📭 Directory is empty.\n"
                return output
            
            # Separate files and directories
            dirs = []
            files = []
            
            for item in immediate_items:
                item_path = os.path.join(abs_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                    total_dirs += 1
                else:
                    files.append(item)
                    total_files += 1
                    try:
                        total_size += os.path.getsize(item_path)
                    except (OSError, IOError):
                        pass  # Skip files we can't access
            
            # Show directories first
            if dirs:
                output += "📂 Directories:\n"
                for d in dirs:
                    dir_path = os.path.join(abs_path, d)
                    try:
                        dir_items = len(os.listdir(dir_path))
                        output += f"   📂 {d}/ ({dir_items} items)\n"
                    except (OSError, PermissionError):
                        output += f"   📂 {d}/ (access denied)\n"
                output += "\n"
            
            # Show files with size info
            if files:
                output += "📄 Files:\n"
                for f in files:
                    file_path = os.path.join(abs_path, f)
                    try:
                        size = os.path.getsize(file_path)
                        # Get file type indication
                        if f.endswith(('.py', '.js', '.ts', '.html', '.css', '.md', '.txt', '.json', '.yaml', '.yml')):
                            icon = "📝"
                        elif f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg')):
                            icon = "🖼️"
                        elif f.endswith(('.mp4', '.avi', '.mov', '.mp3', '.wav')):
                            icon = "🎬"
                        elif f.endswith(('.zip', '.tar', '.gz', '.rar')):
                            icon = "📦"
                        elif f.endswith(('.exe', '.bin', '.dll')):
                            icon = "⚙️"
                        else:
                            icon = "📄"
                        
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.1f} KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f} MB"
                            
                        output += f"   {icon} {f} ({size_str})\n"
                    except (OSError, IOError):
                        output += f"   📄 {f} (size unknown)\n"
            
            # Summary
            output += f"\n📊 Summary: {total_dirs} directories, {total_files} files"
            if total_size > 0:
                if total_size < 1024 * 1024:
                    output += f", {total_size/1024:.1f} KB total"
                else:
                    output += f", {total_size/(1024*1024):.1f} MB total"
            
            return output
            
        except PermissionError:
            return f"Error: Permission denied accessing directory '{path}'"
        except Exception as e:
            return f"Error listing directory contents: {e}"
            
    except Exception as e:
        return f"Error listing files in '{path}': {e}"

def web_search(query: str) -> str:
    """Performs a web search and returns the top results."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
        if not results:
            return "No results found for your query."
        
        output = "Web search results:\n\n"
        for i, result in enumerate(results, 1):
            output += f"[{i}] Title: {result['title']}\n"
            output += f"    URL: {result['href']}\n"
            output += f"    Snippet: {result['body']}\n\n"
        return output.strip()
    except Exception as e:
        return f"Error performing web search: {e}"

def inspect_file(file_path: str) -> str:
    """Inspects a file and returns comprehensive information without reading the full content."""
    try:
        # Get file information
        file_info = get_file_info(file_path)
        
        if not file_info.get("exists", False):
            return f"❌ File '{file_path}' does not exist.\n{file_info.get('error', '')}"
        
        # Build inspection report
        path = Path(file_path)
        abs_path = path.absolute()
        
        output = f"🔍 File Inspection Report for '{file_path}'\n"
        output += f"=" * 50 + "\n\n"
        
        # Basic info
        output += f"📁 Absolute Path: {abs_path}\n"
        output += f"📄 File Name: {path.name}\n"
        output += f"📂 Directory: {path.parent}\n"
        output += f"🔧 Extension: {path.suffix or 'None'}\n\n"
        
        # Size and permissions
        size = file_info.get("size", 0)
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size/(1024*1024):.1f} MB"
        else:
            size_str = f"{size/(1024*1024*1024):.1f} GB"
        
        output += f"📏 Size: {size_str} ({size:,} bytes)\n"
        output += f"👁️ Readable: {'✅' if file_info.get('readable') else '❌'}\n"
        output += f"✏️ Writable: {'✅' if file_info.get('writable') else '❌'}\n\n"
        
        # File type information
        mime_type = file_info.get("mime_type", "unknown")
        is_binary = file_info.get("is_binary", False)
        encoding = file_info.get("encoding")
        
        output += f"📄 MIME Type: {mime_type}\n"
        output += f"🔤 File Type: {'Binary' if is_binary else 'Text'}\n"
        if not is_binary and encoding:
            output += f"🔤 Text Encoding: {encoding}\n"
        output += "\n"
        
        # For text files, show a preview
        if not is_binary and file_info.get("readable") and size > 0:
            try:
                with open(file_path, 'r', encoding=encoding or 'utf-8') as f:
                    # Read first few lines for preview
                    lines = []
                    for i, line in enumerate(f):
                        if i >= 10:  # Show first 10 lines
                            break
                        lines.append(line.rstrip())
                    
                    if lines:
                        output += f"👀 Preview (first {len(lines)} lines):\n"
                        output += "-" * 30 + "\n"
                        for i, line in enumerate(lines, 1):
                            if len(line) > 100:
                                line = line[:97] + "..."
                            output += f"{i:2d}: {line}\n"
                        
                        # Check if there are more lines
                        try:
                            remaining_lines = sum(1 for _ in f)
                            if remaining_lines > 0:
                                output += f"... ({remaining_lines} more lines)\n"
                        except:
                            pass
                        output += "-" * 30 + "\n"
                    else:
                        output += "📄 File appears to be empty or contains only whitespace.\n"
                        
            except Exception as e:
                output += f"⚠️ Could not read file preview: {e}\n"
        
        elif is_binary:
            output += f"🚫 Binary file - cannot show text preview\n"
            output += f"💡 Suggestions for binary files:\n"
            output += f"   • Use 'safe_execute' with 'file {file_path}' for detailed type info\n"
            output += f"   • Use 'safe_execute' with 'xxd {file_path} | head' for hex dump\n"
            output += f"   • Use 'safe_execute' with 'strings {file_path}' to extract text\n"
        
        return output
    
    except Exception as e:
        return f"Error inspecting file '{file_path}': {e}"

def safe_execute(command: str, working_dir: str = None) -> str:
    """Enhanced command execution with better error handling and safety checks."""
    try:
        if not command or not command.strip():
            return "❌ Error: Empty command provided."
        
        # Clean up the command
        command = command.strip()
        
        # Validate working directory if provided
        original_cwd = None
        if working_dir:
            if not os.path.exists(working_dir):
                return f"❌ Error: Working directory '{working_dir}' does not exist."
            if not os.path.isdir(working_dir):
                return f"❌ Error: '{working_dir}' is not a directory."
            original_cwd = os.getcwd()
            os.chdir(working_dir)
        
        # Split command safely
        try:
            split_command = shlex.split(command)
        except ValueError as e:
            return f"❌ Error: Invalid command syntax: {e}"
        
        if not split_command:
            return "❌ Error: Command could not be parsed."
        
        # Execute the command
        try:
            result = subprocess.run(
                split_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=30  # 30-second timeout
            )
            
            # Restore original working directory
            if original_cwd:
                os.chdir(original_cwd)
            
            # Format output
            output = f"🔧 Command: {command}\n"
            if working_dir:
                output += f"📁 Working Directory: {working_dir}\n"
            output += f"🔄 Exit Code: {result.returncode}\n"
            output += "-" * 40 + "\n"
            
            if result.stdout:
                output += f"📤 STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"🚨 STDERR:\n{result.stderr}\n"
            
            if not result.stdout and not result.stderr:
                if result.returncode == 0:
                    output += "✅ Command executed successfully with no output.\n"
                else:
                    output += f"❌ Command failed with exit code {result.returncode} and no output.\n"
            
            return output.rstrip()
            
        except subprocess.TimeoutExpired:
            if original_cwd:
                os.chdir(original_cwd)
            return f"⏱️ Error: Command '{command}' timed out after 30 seconds."
        
        except FileNotFoundError:
            if original_cwd:
                os.chdir(original_cwd)
            return f"❌ Error: Command '{split_command[0]}' not found. Make sure it's installed and in PATH."
        
        except PermissionError:
            if original_cwd:
                os.chdir(original_cwd)
            return f"❌ Error: Permission denied executing '{command}'. Check file permissions."
            
    except Exception as e:
        if 'original_cwd' in locals() and original_cwd:
            os.chdir(original_cwd)
        return f"❌ Error executing command '{command}': {e}"

def replace_in_file(file_path: str, old_text: str, new_text: str) -> str:
    """
    Realiza reemplazo selectivo de texto en un archivo.
    Similar a la herramienta replace_in_file de Cline.
    """
    try:
        # Validar ruta
        is_valid, validation_message = safe_path_validation(file_path)
        if not is_valid:
            return f"❌ Ruta no válida: {validation_message}"
        
        # Leer archivo completo
        file_info = get_file_info(file_path)
        if not file_info["exists"]:
            return f"❌ Archivo no encontrado: {file_path}"
        
        if file_info["is_binary"]:
            return f"❌ No se puede editar archivo binario: {file_path}"
        
        # Leer contenido
        encoding = detect_file_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except Exception as e:
            return f"❌ Error leyendo archivo: {e}"
        
        # Verificar que el texto a reemplazar existe
        if old_text not in content:
            return f"❌ Texto no encontrado en el archivo. Buscado: '{old_text[:100]}...'"
        
        # Contar ocurrencias
        occurrences = content.count(old_text)
        
        # Realizar reemplazo
        new_content = content.replace(old_text, new_text)
        
        # Escribir archivo
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(new_content)
        except Exception as e:
            return f"❌ Error escribiendo archivo: {e}"
        
        # Calcular estadísticas del cambio
        lines_before = len(content.splitlines())
        lines_after = len(new_content.splitlines())
        size_before = len(content)
        size_after = len(new_content)
        
        result = [
            f"✅ Reemplazo exitoso en: {file_path}",
            f"📊 Estadísticas del cambio:",
            f"   • Ocurrencias reemplazadas: {occurrences}",
            f"   • Líneas: {lines_before} → {lines_after} (Δ{lines_after - lines_before:+d})",
            f"   • Tamaño: {size_before:,} → {size_after:,} bytes (Δ{size_after - size_before:+d})",
            f"   • Encoding: {encoding}",
            "",
            f"🔍 Vista previa del cambio:",
            f"   Anterior: '{old_text[:50]}{'...' if len(old_text) > 50 else ''}'",
            f"   Nuevo: '{new_text[:50]}{'...' if len(new_text) > 50 else ''}'"
        ]
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Error inesperado en replace_in_file: {e}"

def search_files(directory: str, regex_pattern: str, file_pattern: str = "*", case_sensitive: bool = True, max_results: int = 50) -> str:
    """
    Busca patrones de texto usando regex en archivos.
    Similar a la herramienta search_files de Cline.
    """
    import re
    import fnmatch
    
    try:
        # Validar directorio
        is_valid, validation_message = safe_path_validation(directory)
        if not is_valid:
            return f"❌ Ruta no válida: {validation_message}"
        
        if not os.path.exists(directory):
            return f"❌ Directorio no encontrado: {directory}"
        
        if not os.path.isdir(directory):
            return f"❌ La ruta no es un directorio: {directory}"
        
        # Compilar regex
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(regex_pattern, flags)
        except re.error as e:
            return f"❌ Patrón regex inválido '{regex_pattern}': {e}"
        
        results = []
        files_searched = 0
        total_matches = 0
        
        # Buscar en archivos
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Filtrar por patrón de archivo
                if not fnmatch.fnmatch(file, file_pattern):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Verificar si es archivo de texto
                file_info = get_file_info(file_path)
                if file_info["is_binary"]:
                    continue
                
                try:
                    files_searched += 1
                    
                    # Leer archivo
                    encoding = detect_file_encoding(file_path)
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    
                    # Buscar matches en cada línea
                    file_matches = []
                    for line_num, line in enumerate(lines, 1):
                        for match in regex.finditer(line.rstrip('\n\r')):
                            file_matches.append({
                                'line': line_num,
                                'content': line.strip(),
                                'match': match.group(0),
                                'start': match.start(),
                                'end': match.end()
                            })
                            total_matches += 1
                            
                            if total_matches >= max_results:
                                break
                        
                        if total_matches >= max_results:
                            break
                    
                    # Añadir archivo a resultados si tiene matches
                    if file_matches:
                        rel_path = os.path.relpath(file_path, directory)
                        results.append({
                            'file': rel_path,
                            'matches': file_matches
                        })
                    
                    if total_matches >= max_results:
                        break
                        
                except Exception as e:
                    # Continuar con otros archivos si hay error
                    continue
            
            if total_matches >= max_results:
                break
        
        # Formatear resultados
        if not results:
            return f"🔍 Búsqueda completada - Sin resultados\n📁 Directorio: {directory}\n🔍 Patrón: {regex_pattern}\n📄 Filtro archivos: {file_pattern}\n📊 Archivos buscados: {files_searched}"
        
        output = [
            f"🔍 Resultados de búsqueda:",
            f"📁 Directorio: {directory}",
            f"🔍 Patrón: {regex_pattern}",
            f"📄 Filtro archivos: {file_pattern}",
            f"📊 Estadísticas:",
            f"   • Archivos buscados: {files_searched}",
            f"   • Archivos con matches: {len(results)}",
            f"   • Total matches: {total_matches}",
            f"   • Límite alcanzado: {'Sí' if total_matches >= max_results else 'No'}",
            ""
        ]
        
        for result in results[:20]:  # Mostrar máximo 20 archivos
            output.append(f"📄 {result['file']}:")
            for match in result['matches'][:5]:  # Máximo 5 matches por archivo
                output.append(f"   Línea {match['line']:4d}: {match['content']}")
                spaces = ' ' * match['start']
                arrows = '^' * len(match['match'])
                output.append(f"              {spaces}{arrows} <- '{match['match']}'")
            
            if len(result['matches']) > 5:
                output.append(f"   ... y {len(result['matches']) - 5} matches más")
            output.append("")
        
        if len(results) > 20:
            output.append(f"... y {len(results) - 20} archivos más con matches")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error inesperado en search_files: {e}"

def list_code_definition_names(file_path: str, language: str = "auto") -> str:
    """
    Lista nombres de definiciones de código (funciones, clases, métodos).
    Similar a la herramienta list_code_definition_names de Cline.
    """
    import re
    
    try:
        # Validar archivo
        is_valid, validation_message = safe_path_validation(file_path)
        if not is_valid:
            return f"❌ Ruta no válida: {validation_message}"
        
        file_info = get_file_info(file_path)
        if not file_info["exists"]:
            return f"❌ Archivo no encontrado: {file_path}"
        
        if file_info["is_binary"]:
            return f"❌ No se puede analizar archivo binario: {file_path}"
        
        # Detectar lenguaje automáticamente si no se especifica
        if language == "auto":
            ext = os.path.splitext(file_path)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript', 
                '.ts': 'typescript',
                '.jsx': 'javascript',
                '.tsx': 'typescript',
                '.java': 'java',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'csharp',
                '.php': 'php',
                '.rb': 'ruby',
                '.go': 'go',
                '.rs': 'rust'
            }
            language = language_map.get(ext, 'unknown')
        
        # Leer archivo
        encoding = detect_file_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        lines = content.splitlines()
        definitions = []
        
        # Patrones de regex por lenguaje
        patterns = {
            'python': [
                (r'^(class\s+(\w+).*?):', 'class'),
                (r'^(\s*def\s+(\w+).*?):', 'function'),
                (r'^(\s*async\s+def\s+(\w+).*?):', 'async_function')
            ],
            'javascript': [
                (r'(class\s+(\w+).*?)\s*{', 'class'),
                (r'(function\s+(\w+).*?)\s*{', 'function'),
                (r'((\w+)\s*:\s*function.*?)\s*{', 'method'),
                (r'((\w+)\s*=>\s*)', 'arrow_function'),
                (r'(const\s+(\w+)\s*=.*?=>\s*)', 'const_arrow_function')
            ],
            'typescript': [
                (r'(class\s+(\w+).*?)\s*{', 'class'),
                (r'(function\s+(\w+).*?)\s*{', 'function'),
                (r'((\w+)\s*:\s*function.*?)\s*{', 'method'),
                (r'((\w+)\s*=>\s*)', 'arrow_function'),
                (r'(const\s+(\w+)\s*=.*?=>\s*)', 'const_arrow_function'),
                (r'(interface\s+(\w+).*?)\s*{', 'interface'),
                (r'(type\s+(\w+).*?=)', 'type')
            ],
            'java': [
                (r'(class\s+(\w+).*?)\s*{', 'class'),
                (r'(interface\s+(\w+).*?)\s*{', 'interface'),
                (r'(\w+\s+(\w+)\s*\([^)]*\)\s*{)', 'method')
            ],
            'cpp': [
                (r'(class\s+(\w+).*?)\s*{', 'class'),
                (r'(struct\s+(\w+).*?)\s*{', 'struct'),
                (r'(\w+\s+(\w+)\s*\([^)]*\)\s*{)', 'function')
            ]
        }
        
        # Obtener patrones para el lenguaje
        lang_patterns = patterns.get(language, patterns.get('javascript', []))
        
        # Buscar definiciones
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            
            for pattern, def_type in lang_patterns:
                match = re.search(pattern, line)
                if match:
                    full_def = match.group(1)
                    name = match.group(2) if match.lastindex >= 2 else "unknown"
                    
                    definitions.append({
                        'name': name,
                        'type': def_type,
                        'line': line_num,
                        'definition': full_def.strip()
                    })
        
        # Formatear resultados
        if not definitions:
            return f"🔍 Análisis de código completado - Sin definiciones encontradas\n📄 Archivo: {file_path}\n🌐 Lenguaje: {language}\n📊 Líneas analizadas: {len(lines)}"
        
        # Agrupar por tipo
        by_type = {}
        for defn in definitions:
            if defn['type'] not in by_type:
                by_type[defn['type']] = []
            by_type[defn['type']].append(defn)
        
        output = [
            f"🔍 Definiciones de código encontradas:",
            f"📄 Archivo: {file_path}",
            f"🌐 Lenguaje: {language}",
            f"📊 Total definiciones: {len(definitions)}",
            f"📏 Líneas totales: {len(lines)}",
            ""
        ]
        
        # Mostrar por tipo
        type_icons = {
            'class': '🏛️',
            'function': '⚙️',
            'method': '🔧',
            'async_function': '⚡',
            'arrow_function': '➡️',
            'const_arrow_function': '📌',
            'interface': '🔌',
            'type': '📝',
            'struct': '🏗️'
        }
        
        for def_type, defs in by_type.items():
            icon = type_icons.get(def_type, '📄')
            output.append(f"{icon} {def_type.upper()} ({len(defs)}):")
            
            for defn in defs:
                output.append(f"   Línea {defn['line']:4d}: {defn['name']}")
                if len(defn['definition']) <= 80:
                    output.append(f"              {defn['definition']}")
                else:
                    output.append(f"              {defn['definition'][:77]}...")
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error inesperado en list_code_definition_names: {e}"

def attempt_completion(result: str) -> str:
    """A tool to signal that the task is complete."""
    # This function's output is handled specially in main.py.
    return f"Task completed. Result: {result}"

# Importar funciones de módulos especializados
from bytecrafter.browser_tools import (
    start_browser_session, navigate_browser, take_browser_screenshot, close_browser_session
)
from bytecrafter.task_manager import (
    new_task, start_task_work, complete_current_task, break_down_current_task, 
    show_task_list, show_current_task
)

# Declaraciones de las nuevas herramientas avanzadas
replace_in_file_declaration = genai.protos.FunctionDeclaration(
    name="replace_in_file",
    description="Realiza reemplazo selectivo de texto en un archivo. Similar a la herramienta replace_in_file de Cline.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "file_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="Ruta del archivo a editar."),
            "old_text": genai.protos.Schema(type=genai.protos.Type.STRING, description="Texto a reemplazar en el archivo."),
            "new_text": genai.protos.Schema(type=genai.protos.Type.STRING, description="Nuevo texto que reemplazará al anterior.")
        },
        required=["file_path", "old_text", "new_text"]
    )
)

search_files_declaration = genai.protos.FunctionDeclaration(
    name="search_files",
    description="Busca patrones de texto usando regex en archivos. Similar a la herramienta search_files de Cline.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "directory": genai.protos.Schema(type=genai.protos.Type.STRING, description="Directorio donde buscar."),
            "regex_pattern": genai.protos.Schema(type=genai.protos.Type.STRING, description="Patrón regex a buscar."),
            "file_pattern": genai.protos.Schema(type=genai.protos.Type.STRING, description="Patrón de archivos a incluir (ej: '*.py'). Default: '*'"),
            "case_sensitive": genai.protos.Schema(type=genai.protos.Type.BOOLEAN, description="Si la búsqueda es sensible a mayúsculas. Default: true"),
            "max_results": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Máximo número de resultados. Default: 50")
        },
        required=["directory", "regex_pattern"]
    )
)

list_code_definition_names_declaration = genai.protos.FunctionDeclaration(
    name="list_code_definition_names",
    description="Lista nombres de definiciones de código (funciones, clases, métodos). Similar a la herramienta list_code_definition_names de Cline.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "file_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="Ruta del archivo de código a analizar."),
            "language": genai.protos.Schema(type=genai.protos.Type.STRING, description="Lenguaje de programación ('auto', 'python', 'javascript', etc.). Default: 'auto'")
        },
        required=["file_path"]
    )
)

ask_followup_question_declaration = genai.protos.FunctionDeclaration(
    name="ask_followup_question",
    description="Herramienta mejorada para hacer preguntas de seguimiento al usuario con opciones múltiples.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "question": genai.protos.Schema(type=genai.protos.Type.STRING, description="La pregunta a hacer al usuario."),
            "options": genai.protos.Schema(type=genai.protos.Type.STRING, description="Opciones separadas por comas (ej: 'Sí,No,Tal vez'). Opcional.")
        },
        required=["question"]
    )
)

# Declaraciones para herramientas del navegador
start_browser_session_declaration = genai.protos.FunctionDeclaration(
    name="start_browser_session",
    description="Inicia una sesión de navegador Chrome con CDP habilitado para testing web y automatización.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "headless": genai.protos.Schema(type=genai.protos.Type.BOOLEAN, description="Si ejecutar el navegador en modo headless. Default: true")
        },
        required=[]
    )
)

navigate_browser_declaration = genai.protos.FunctionDeclaration(
    name="navigate_browser",
    description="Navega el navegador a una URL específica.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "url": genai.protos.Schema(type=genai.protos.Type.STRING, description="URL a la que navegar (con o sin protocolo http/https).")
        },
        required=["url"]
    )
)

take_browser_screenshot_declaration = genai.protos.FunctionDeclaration(
    name="take_browser_screenshot",
    description="Toma una captura de pantalla de la página actual del navegador.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "save_path": genai.protos.Schema(type=genai.protos.Type.STRING, description="Ruta donde guardar la imagen. Si no se especifica, se genera automáticamente.")
        },
        required=[]
    )
)

close_browser_session_declaration = genai.protos.FunctionDeclaration(
    name="close_browser_session",
    description="Cierra la sesión del navegador y libera recursos.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={},
        required=[]
    )
)

# Declaraciones para sistema de gestión de tareas
new_task_declaration = genai.protos.FunctionDeclaration(
    name="new_task",
    description="Crea una nueva tarea. Similar a la herramienta new_task de Cline para dividir trabajos complejos.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "description": genai.protos.Schema(type=genai.protos.Type.STRING, description="Descripción de la tarea."),
            "priority": genai.protos.Schema(type=genai.protos.Type.STRING, description="Prioridad de la tarea: 'low', 'medium', 'high', 'urgent'. Default: 'medium'"),
            "parent_task_id": genai.protos.Schema(type=genai.protos.Type.STRING, description="ID de la tarea padre si es una subtarea."),
            "tags": genai.protos.Schema(type=genai.protos.Type.STRING, description="Tags separados por comas para categorizar la tarea.")
        },
        required=["description"]
    )
)

start_task_work_declaration = genai.protos.FunctionDeclaration(
    name="start_task_work",
    description="Inicia trabajo en una tarea específica.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "task_id": genai.protos.Schema(type=genai.protos.Type.STRING, description="ID de la tarea a iniciar.")
        },
        required=["task_id"]
    )
)

complete_current_task_declaration = genai.protos.FunctionDeclaration(
    name="complete_current_task",
    description="Completa la tarea actual en progreso.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "notes": genai.protos.Schema(type=genai.protos.Type.STRING, description="Notas opcionales sobre la completación de la tarea.")
        },
        required=[]
    )
)

break_down_current_task_declaration = genai.protos.FunctionDeclaration(
    name="break_down_current_task",
    description="Divide la tarea actual en subtareas más pequeñas y manejables.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "subtask_descriptions": genai.protos.Schema(type=genai.protos.Type.STRING, description="Descripciones de subtareas separadas por comas.")
        },
        required=["subtask_descriptions"]
    )
)

show_task_list_declaration = genai.protos.FunctionDeclaration(
    name="show_task_list",
    description="Muestra lista de tareas con filtros opcionales.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "status": genai.protos.Schema(type=genai.protos.Type.STRING, description="Filtrar por estado: 'pending', 'in_progress', 'completed', 'failed'.")
        },
        required=[]
    )
)

show_current_task_declaration = genai.protos.FunctionDeclaration(
    name="show_current_task",
    description="Muestra información de la tarea actual en progreso.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={},
        required=[]
    )
)

# ------------------------- MCP INTEGRATION -------------------------

# Declaración para registrar un servidor MCP
mcp_add_server_declaration = genai.protos.FunctionDeclaration(
    name="mcp_add_server",
    description="Registra un servidor MCP local (STDIO). El comando puede ser una ruta a script .py o un ejecutable.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Nombre único del servidor."),
            "command": genai.protos.Schema(type=genai.protos.Type.STRING, description="Comando para lanzar el servidor (ej: 'python server.py').")
        },
        required=["name", "command"]
    )
)


def mcp_add_server(name: str, command: str) -> str:
    """Agrega un servidor MCP al registro global."""
    try:
        from bytecrafter.mcp import server_registry
        server_registry.add_server(name, command)
        return f"✅ Servidor '{name}' registrado con comando '{command}'."
    except Exception as e:
        return f"❌ Error al registrar servidor MCP: {e}"


# Declaración para listar servidores MCP
mcp_list_servers_declaration = genai.protos.FunctionDeclaration(
    name="mcp_list_servers",
    description="Lista los servidores MCP registrados.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={},
        required=[]
    )
)


def mcp_list_servers() -> str:
    """Devuelve la lista de servidores MCP registrados."""
    try:
        from bytecrafter.mcp import server_registry
        data = server_registry.list_servers()
        if not data:
            return "No hay servidores MCP registrados."
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"❌ Error al listar servidores MCP: {e}"


# Declaración para ejecutar una herramienta MCP genérica
mcp_execute_tool_declaration = genai.protos.FunctionDeclaration(
    name="mcp_execute_tool",
    description="Ejecuta una herramienta expuesta por un servidor MCP registrado.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "server_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Nombre del servidor MCP registrado."),
            "tool_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Nombre de la herramienta dentro del servidor."),
            "params_json": genai.protos.Schema(type=genai.protos.Type.STRING, description="Parámetros JSON como string para la herramienta. Opcional.")
        },
        required=["server_name", "tool_name"]
    )
)


def mcp_execute_tool(server_name: str, tool_name: str, params_json: str = "{}") -> str:
    """Ejecuta una herramienta MCP usando transporte STDIO."""
    try:
        from bytecrafter.mcp import server_registry, transport_stdio
        command = server_registry.get_server_command(server_name)
        if not command:
            return f"❌ Servidor '{server_name}' no encontrado."
        try:
            params = json.loads(params_json) if params_json else {}
        except json.JSONDecodeError:
            return "❌ params_json no es un JSON válido."

        client = transport_stdio.StdioClient(command)
        try:
            response = client.send_request(tool_name, params, timeout=20)
        finally:
            client.close()
        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"❌ Error al ejecutar herramienta MCP: {e}" 