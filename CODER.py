from __future__ import annotations

# --- STANDARD LIBRARIES ---
import os
import sys
import re
import glob
import json
import time
import random
import ast
import subprocess
import shutil
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Annotated, List, Dict, Any, Optional, Union, Literal

# --- THIRD-PARTY CORE ---
import ollama
import chromadb
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from sentence_transformers import SentenceTransformer

# --- LANGCHAIN & AGENTICS ---
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START

# --- RICH UI ENGINE (NEW) ---
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.theme import Theme
from rich.status import Status
from rich.table import Table
from rich.align import Align
import contextlib

# --- VISUAL DESIGN CONSTANTS (MONOCHROMATIC) ---
# Moon phases for the node animation
MOON_PHASES = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]

# Strict Monochromatic Theme: White, Grey variants, and Red for errors only.
CODER_THEME = Theme({
    "primary": "white",          # High emphasis text/headers
    "dim": "grey37",             # Low emphasis / borders
    "subtle": "grey70",          # Metadata / secondary info
    "error": "red",              # Critical failures only
    "accent": "white",           # UI accents
    "border": "grey37",          # Panel borders
    "bg": "black"                # Background consistency
})

# Global Console instance for the entire agent
console = Console(theme=CODER_THEME)

class ToolCall(BaseModel):
    """Schema for a tool execution."""
    tool_name: str = Field(description="The name of the tool to use")
    arguments: Dict[str, Any] = Field(description="The arguments for the tool as a dictionary")

class AgentResponse(BaseModel):
    """The mandatory structure for every LLM response."""
    trajectory: str = Field(description="Current step/roadmap: [Step X/Y | Task -> Next Target -> Ultimate Objective]")
    synthesis: str = Field(description="Your deep reasoning, error analysis, or 'REQUEST_GUIDANCE' signal")
    action: Optional[ToolCall] = Field(description="The tool to call, or null if finishing")
    completion_summary: Optional[str] = Field(description="Final technical summary of the mission results")

class AgentState(TypedDict):
    mission: str
    trajectory: str
    synthesis: str
    last_observation: str
    history: List[Dict[str, str]]
    next_step: str
    current_node: str
    error_count: int
    is_finished: bool
    pending_action: Optional[ToolCall]
    consecutive_reasoning_steps: int
    memory_context: str

# --- 1. MINIMALIST ARCHITECTURAL UI ---

class RichUI:
    """A high-end monochromatic interface using Rich for structural beauty."""
    
    def __init__(self):
        self.console = Console(theme=CODER_THEME, force_terminal=True)
        self.status_msg = "Idle"

    @contextlib.contextmanager
    def node_context(self, name: str, is_error: bool = False):
        """
        The Core Visual Engine. 
        Now respects 'is_error' for its default completion state.
        """
        border_style = "error" if is_error else "border"
        title_text = Text(f" {name.upper()} ", style="primary")
        content = Align.center(Text("Initializing...", style="subtle"), vertical="middle")
        panel = Panel(content, title=title_text, border_style=border_style, padding=(1, 2))

        with Live(panel, console=self.console, refresh_per_second=12) as live:
            phase_idx = 0
            stop_animation = False
            customized = False 

            def animate():
                nonlocal phase_idx
                while not stop_animation:
                    moon = MOON_PHASES[phase_idx % len(MOON_PHASES)]
                    new_content = Align.center(
                        Text(f"{moon} {self.status_msg}", style="subtle"), 
                        vertical="middle"
                    )
                    if not customized:
                        live.update(Panel(new_content, title=title_text, border_style=border_style, padding=(1, 2)))
                    phase_idx += 1
                    time.sleep(0.15)

            class LiveProxy:
                def update(self, renderable):
                    nonlocal customized
                    customized = True
                    stop_animation = True # Kill animation immediately on manual update
                    live.update(renderable)

            proxy = LiveProxy()
            anim_thread = threading.Thread(target=animate, daemon=True)
            anim_thread.start()
            
            try:
                yield proxy  
                stop_animation = True
                anim_thread.join(timeout=0.2)

                if not customized:
                    # --- FIX: If it was an error node, show RED 'RECOVERY' instead of GREEN 'COMPLETED' ---
                    if is_error:
                        final_content = Align.center(Text("⚠ RECOVERY INITIATED", style="white"), vertical="middle")
                        live.update(Panel(final_content, title=title_text, border_style="error", padding=(1, 2)))
                    else:
                        # UPDATED: Changed from "✓ COMPLETED" to "COMPLETED✅"
                        final_content = Align.center(Text("COMPLETED✅", style="green"), vertical="middle")
                        live.update(Panel(final_content, title=title_text, border_style="green", padding=(1, 2)))
                
            except Exception as e:
                stop_animation = True
                anim_thread.join(timeout=0.2)
                final_content = Align.center(Text(f"✕ FAILED", style="error"), vertical="middle")
                live.update(Panel(final_content, title=title_text, border_style="error", padding=(1, 2)))
                raise e

    def _force_clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.console.clear()

    def _matrix_rain(self, duration: float = 1.5):
        """
        High-intensity, ultra-fast digital rain.
        Creates a dense 'wall' of characters with minimal gaps and rapid scrolling.
        """
        columns, lines = shutil.get_terminal_size()
        # Using a more focused set of characters
        chars = "0123456789ABCDEFHIJKLMNOPQRSTUVWXYZ$+-*/=%#&"
        start_time = time.time()
        
        #prevent flickering
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

        try:
            while time.time() - start_time < duration:
                line_buffer = []
                for _ in range(columns):
                    # HIGH DENSITY: 90% chance of a character, only 10% chance of a space
                    if random.random() > 0.1:
                        char = random.choice(chars)
                        # Faster color selection logic
                        color_roll = random.random()
                        if color_roll > 0.9:
                            color = "green"
                        elif color_roll > 0.7:
                            color = "green"        # Standard green
                        else:
                            color = "green" 
                        
                        line_buffer.append(f"[{color}]{char}[/]")
                    else:
                        line_buffer.append(" ")
                
                # Join the entire line into one string before printing to minimize I/O calls
                self.console.print("".join(line_buffer))
                
                # ULTRA FAST: Minimal sleep for that 'blur' effect
                time.sleep(0.001) 
                
        finally:
            # Always restore visibility
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

    def startup_sequence(self):
        
        self._force_clear()
        word = "Hello, World!"
        
        # Ensure we are at the top left
        print("\n" * 2, end="")

        
        for char in word:
            self.console.print(char, end="", style="green")
            sys.stdout.flush()
            time.sleep(0.3)  # Slow speed

        time.sleep(2.0)

        for _ in range(len(word)):
            sys.stdout.write('\b \b') # Move back, print space to clear, move back again
            sys.stdout.flush()
            time.sleep(0.01)

        
        self._force_clear()
        self._matrix_rain(duration=2.5)
        
        self._force_clear()
            
        
        
        self.console.print("\n", end="")

    def boot(self):
        self.console.clear()
        ts = datetime.now().strftime('%H:%M:%S')
        self.console.print(f"[dim]{ts} | SYSTEM ONLINE[/dim]\n")

    def select_model(self):
        self.console.clear()
        self.console.print("[subtle]Scanning available layers...[/subtle]")
        try:
            output = subprocess.check_output(['ollama', 'list'], text=True)
            lines = output.strip().split('\n')
            if len(lines) <= 1: return None
            models = [line.split()[0] for line in lines[1:] if line.split()]
            self.console.print("\n[primary]AVAILABLE LAYERS:[/primary]")
            for i, model in enumerate(models):
                self.console.print(f"[dim]{i+1}.[/dim] [white]{model}[/white]")
            self.console.print("") 
            self.console.print("[primary]❯ [/primary]", end="")
            sys.stdout.flush()
            choice = input()
            return models[int(choice) - 1]
        except Exception: return None

    def update_status(self, msg: str): self.status_msg = msg

    def log_thought(self, text: str):
        self.console.print(f"\n[primary]THOUGHT:[/primary]")
        self.console.print(f"  [subtle]{text.replace('\n', '\n  ')}[/subtle]")

    def log_action(self, tool: str, args: dict):
        arg_str = f"({args})" if args else ""
        self.console.print(f"\n[primary]ACTION:[/primary] [white]{tool.upper()} {arg_str}[/white]")

    def log_observation(self, text: str):
        self.console.print(f"  [subtle]↳[/subtle] [subtle]{text}[/subtle]")

    def log_briefing(self, title: str, content: str):
        self.console.print(f"\n[primary]{title}[/primary]\n[subtle]{content}[/subtle]\n")

    def log_final(self, text: str):
        self.console.print(f"\n[primary]SYNTHESIS:[/primary]")
        for line in text.split('\n'):
            if line.strip(): self.console.print(f"  [subtle]{line}[/subtle]")

    def log_error(self, text: str): self.console.print(f"\n[error][!] ERROR: {text}[/error]")

    def ask_user(self, question: str) -> str:
        self.console.print(f"\n[error][!] INTERVENTION REQUIRED:[/error] [white]{question}[/white]")
        self.console.print("[primary]❯ [/primary]", end="")
        sys.stdout.flush()
        return input()

    def log_system_status(self, msg: str): self.console.print(f"[dim][SYSTEM]: {msg}[/dim]")

    def log_mission_success(self): self.console.print("\n[primary]MISSION OBJECTIVE ACHIEVED.[/primary]")

# --- 2. THE TOOLBOX ---

class Toolbox:
    @staticmethod
    def list_files(directory=".", **kwargs):
        """Performs a deep scan of the target directory, returning detailed file metadata."""
        try:
            target = directory or kwargs.get('path') or kwargs.get('dir') or "."
            if not os.path.exists(target): return f"ERROR: Path '{target}' does not exist."
            
            items = os.listdir(target)
            report = []
            for item in items:
                full_path = os.path.join(target, item)
                stats = os.stat(full_path)
                is_dir = os.path.isdir(full_path)
                size = stats.st_size
                mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                report.append(f"[{'DIR' if is_dir else 'FILE'}] {item} | Size: {size}B | Modified: {mod_time}")
            
            return f"SUCCESS: Found {len(items)} items in '{target}':\n" + "\n".join(report)
        except Exception as e: return f"ERROR: Directory Scan Failed: {e}"

    @staticmethod
    def get_tree(directory=".", max_depth=3, **kwargs):
        """Generates a visual structural representation of the filesystem with depth control."""
        def _build_tree(path, prefix="", depth=0):
            if depth > max_depth: return ""
            tree = ""
            try:
                items = sorted([i for i in os.listdir(path) if not i.startswith('.')])
                for i, item in enumerate(items):
                    is_last = (i == len(items) - 1)
                    connector = "└── " if is_last else "├── "
                    tree += f"{prefix}{connector}{item}\n"
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        extension = "    " if is_last else "│   "
                        tree += _build_tree(full_path, prefix + extension, depth + 1)
                return tree
            except Exception: return ""
        try: 
            target = directory or kwargs.get('path') or "."
            return f"SUCCESS: Project Structure (Max Depth {max_depth}):\n{_build_tree(target)}"
        except Exception as e: return f"ERROR: Tree Generation Failed: {e}"

    @staticmethod
    def read_file(filename=None, start_line=1, end_line=None, **kwargs):
        """Surgically reads file content with support for line-range extraction and encoding fallback."""
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            if not target: return "ERROR: Missing filename."
            
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            for enc in encodings:
                try:
                    with open(target, "r", encoding=enc) as f:
                        lines = f.readlines()
                    content = lines
                    break
                except (UnicodeDecodeError, LookupError): continue
            
            if content is None: return "ERROR: Unable to decode file with supported encodings."

            # Line slicing logic
            s_idx = max(0, start_line - 1)
            e_idx = end_line if end_line else len(content)
            selected_lines = content[s_idx:e_idx]
            
            output = "".join(selected_lines).strip()
            meta = f"Lines {start_line}-{e_idx} | Total Lines: {len(content)} | Encoding: {enc}"
            return f"SUCCESS: [{meta}]\n{output[:10000]}" # Safety cap at 10k chars
        except Exception as e: return f"ERROR: Read Failure: {e}"

    @staticmethod
    def write_file(filename=None, content=None, mode="overwrite", **kwargs):
        """Atomic-style file writing. Supports 'overwrite' and 'create_new' modes."""
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            body = content or kwargs.get('text') or kwargs.get('body')
            if not target or body is None: return "ERROR: Missing parameters."
            
            mode = mode or kwargs.get('mode', 'overwrite')
            
            if mode == "create_new" and os.path.exists(target):
                return f"ERROR: File '{target}' already exists. Use 'overwrite' to replace."

            with open(target, "w", encoding='utf-8') as f: 
                f.write(str(body))
            return f"SUCCESS: File '{target}' written via {mode} mode."
        except Exception as e: return f"ERROR: Write Failure: {e}"

    @staticmethod
    def append_to_file(filename=None, content=None, **kwargs):
        """Appends content to the end of a file with automatic newline handling."""
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            body = content or kwargs.get('text') or kwargs.get('body')
            if not target or body is None: return "ERROR: Missing parameters."
            with open(target, "a", encoding='utf-8') as f: 
                f.write(f"\n{str(body)}")
            return f"SUCCESS: Content appended to '{target}'."
        except Exception as e: return f"ERROR: Append Failure: {e}"

    @staticmethod
    def replace_in_file(filename=None, search_pattern=None, replacement=None, use_regex=False, **kwargs):
        """Advanced text replacement. Can use standard strings or Regex patterns for complex edits."""
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            search = search_pattern or kwargs.get('search')
            rep = replacement or kwargs.get('replace')
            if not target or not search or rep is None: return "ERROR: Missing parameters."
            
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                data = f.read()
            
            if use_regex:
                import re
                new_data = re.sub(search, rep, data)
            else:
                new_data = data.replace(search, rep)
            
            if data == new_data: return "ERROR: No matches found for replacement."
                
            with open(target, 'w', encoding='utf-8') as f:
                f.write(new_data)
            return f"SUCCESS: Transformation complete in {target}."
        except Exception as e: return f"ERROR: Replace Failure: {e}"

    # --- CODE INTELLIGENCE & ANALYSIS ---

    @staticmethod
    def analyze_code_structure(filename=None, **kwargs):
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            with open(target, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            structure = {"classes": [], "functions": [], "imports": []}
            for node in tree.body: # Iterate only top-level nodes
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    structure["classes"].append({"name": node.name, "methods": methods})
                elif isinstance(node, ast.FunctionDef):
                    structure["functions"].append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    structure["imports"].append(ast.dump(node))

            return f"SUCCESS: Logical Map of {target}:\n{json.dumps(structure, indent=2)}"
        except Exception as e: return f"ERROR: AST Analysis Failed: {e}"

    @staticmethod
    def python_executor(code=None, **kwargs):
        import os, sys, subprocess, tempfile, traceback, re
        clean_code = code or kwargs.get('script') or kwargs.get('command') or kwargs.get('code')
        if not clean_code: return "ERROR: No valid code detected."

        # PATCH 2: Fixed incomplete regex and added re.DOTALL for multi-line code blocks
        blocks = re.findall(r"```(?:python)?\s*(.*?)\s*```", clean_code, re.DOTALL)
        if blocks: clean_code = blocks[-1].strip()


        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as tmp:
                tmp.write(clean_code)
                tmp_path = tmp.name

            result = subprocess.run([sys.executable, tmp_path], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return f"ERROR: Execution Failed (Code {result.returncode})\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            return f"SUCCESS: Output:\n{result.stdout}\n{f'STDERR: {result.stderr}' if result.stderr else ''}"
        except Exception as e: return f"ERROR: Engine Failure: {traceback.format_exc()}"
        finally:
            if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)

    # --- SYSTEM & NETWORK ORCHESTRATION ---

    @staticmethod
    def get_system_info():
        """Returns a comprehensive snapshot of the host environment."""
        import platform, psutil # Note: Requires psutil if installed, else falls back to platform
        try:
            info = {
                "os": f"{platform.system()} {platform.release()}",
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "cpu_count": os.cpu_count(),
                "cwd": os.getcwd(),
                "user": os.getlogin() if os.name != 'nt' else os.environ.get('USERNAME')
            }
            # Try adding memory/disk via psutil if available
            try:
                import psutil
                info["memory_total"] = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
                info["disk_usage"] = f"{psutil.disk_usage('/').percent}%"
            except ImportError: pass
            return f"SUCCESS: System Manifest:\n{json.dumps(info, indent=2)}"
        except Exception as e: return f"ERROR: System Info Failed: {e}"

    @staticmethod
    def shell_execute(command):
        """Executes low-level system commands with full terminal capability."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=45)
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        except Exception as e: return f"ERROR: Shell Execution Failed: {e}"

    @staticmethod
    def manage_process(action, pid=None, **kwargs):
        """Orchestrates system processes (list, kill). action='list' or 'kill'."""
        try:
            if action == "list":
                import subprocess
                cmd = "tasklist" if os.name == 'nt' else "ps aux"
                res = subprocess.check_output(cmd, shell=True, text=True)
                return f"SUCCESS: Process List:\n{res[:5000]}"
            elif action == "kill":
                if not pid: return "ERROR: PID required for kill action."
                import os, signal
                if os.name == 'nt':
                    os.system(f"taskkill /F /PID {pid}")
                else:
                    os.kill(int(pid), signal.SIGKILL)
                return f"SUCCESS: Process {pid} terminated."
            return "ERROR: Invalid action. Use 'list' or 'kill'."
        except Exception as e: return f"ERROR: Process Management Failed: {e}"

    # --- MATHEMATICAL & DATA COMPUTATION ---

    @staticmethod
    def scientific_compute(expression):
        """Performs high-precision symbolic and arithmetic computation."""
        import math
        from decimal import Decimal, getcontext
        getcontext().prec = 60 
        safe_namespace = {
            "math": math, "Decimal": Decimal, "pi": math.pi, "e": math.e, 
            "sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt,
            "log": math.log, "exp": math.exp
        }
        try:
            # Using eval is risky but in this agent context, it's the 'executor' role
            result = eval(expression, {"__builtins__": None}, safe_namespace)
            return f"SUCCESS: Computed Result = {result}"
        except Exception as e: return f"ERROR: Math Engine Error: {e}"

    @staticmethod
    def search_files(pattern, **kwargs):
        """Finds files matching a glob pattern recursively."""
        try:
            target = kwargs.get('directory', '.')
            matches = glob.glob(f"{target}/**/{pattern}", recursive=True)
            return f"SUCCESS: Found {len(matches)} matches:\n" + "\n".join(matches)
        except Exception as e: return f"ERROR: Search Failed: {e}"

    @staticmethod
    def grep_search(pattern, file_path, context_lines=3, **kwargs):
        """Searches for a pattern within a file and returns the matching lines with surrounding context."""
        try:
            target = file_path or kwargs.get('path') or kwargs.get('file')
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            results = []
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    context = lines[start:end]
                    results.append(f"--- Match at Line {i+1} ---\n" + "".join(context))
            
            if not results: return "SUCCESS: No matches found."
            return f"SUCCESS: Found {len(results)} match blocks:\n" + "\n".join(results[:5])
        except Exception as e: return f"ERROR: Grep Failed: {e}"
    
    @staticmethod
    def run_file(filename):
        """Executes a specific python file using the current system interpreter."""
        try:
            import sys, subprocess
            # We use sys.executable to ensure we use the same environment the agent is running in
            result = subprocess.run([sys.executable, filename], capture_output=True, text=True, timeout=30)
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        except Exception as e: 
            return f"ERROR: Failed to execute file '{filename}': {e}"

    @staticmethod
    def ask_user(question):
        """Directly interrupts the autonomous loop to request human intervention."""
        print(f"\n{'\033[93m'}[!] AGENT INTERVENTION REQUIRED: {question}\033[0m")
        return f"USER RESPONSE: {input('❯ ')}"

    @staticmethod
    def get_file_stats(filename=None, **kwargs):
        """Provides deep-dive metadata for a specific file (permissions, size, timestamps)."""
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            s = os.stat(target)
            return f"SUCCESS: Stats for {target}:\nSize: {s.st_size}B\nCreated: {datetime.fromtimestamp(s.st_ctime)}\nModified: {datetime.fromtimestamp(s.st_mtime)}\nMode: {oct(s.st_mode)}"
        except Exception as e: return f"ERROR: Stats Failed: {e}"

# --- AST-BASED STRUCTURAL INTELLIGENCE TOOLS ---

    @staticmethod
    def extract_logic_block(filename=None, target_name=None, target_type="function", **kwargs):
        """
        [AST TOOL: LOGIC EXTRACTION]
        Surgically extracts a specific block of code (function or class) from a file.
        This prevents context window overflow by allowing the agent to focus 
        ONLY on the relevant logical unit.
        
        Args:
            target_name (str): The name of the function or class to extract.
            target_type (str): 'function' or 'class'.
        """
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            if not target: return "ERROR: Missing filename."
            if not target_name: return "ERROR: Target name required for extraction."

            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            extracted_code = ""
            found = False

            for node in ast.walk(tree):
                # Check for Function extraction
                if target_type == "function" and isinstance(node, ast.FunctionDef):
                    if node.name == target_name:
                        extracted_code = ast.get_source_segment(source, node)
                        found = True
                        break
                # Check for Class extraction
                elif target_type == "class" and isinstance(node, ast.ClassDef):
                    if node.name == target_name:
                        extracted_code = ast.get_source_segment(source, node)
                        found = True
                        break

            if not found:
                return f"ERROR: Could not find {target_type} '{target_name}' in {target}</code_analysis>"
            
            return f"SUCCESS: Extracted {target_type} '{target_name}':\n{extracted_code}"
        except Exception as e:
            return f"ERROR: AST Extraction Failure: {e}"

    @staticmethod
    def lint_and_validate(code=None, **kwargs):
        """
        [AST TOOL: PRE-FLIGHT VALIDATION]
        Performs a static analysis of the provided code snippet to detect 
        syntax errors and logical red flags BEFORE execution.
        """
        clean_code = code or kwargs.get('script') or kwargs.get('code')
        if not clean_code: return "ERROR: No code provided for validation."

        try:
            # 1. Syntax Check
            tree = ast.parse(clean_code)
            
            # 2. Complexity/Safety Analysis
            issues = []
            for node in ast.walk(tree):
                # Detect dangerous imports if needed (example)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['os', 'subprocess', 'shutil']:
                            issues.append(f"WARNING: Use of system-level module '{alias.name}' detected.")
                
                # Detect deep nesting (Complexity check)
                if isinstance(node, (ast.For, ast.While)):
                    # This is a simplified check for demonstration
                    pass 

            if not issues:
                return "SUCCESS: Code is syntactically valid and passed basic safety checks."
            else:
                return "VALIDATION_REPORT:\n" + "\n".join([f"- {i}" for i in issues])

        except SyntaxError as se:
            return f"ERROR: Syntax Error detected at line {se.lineno}, offset {se.offset}: {se.msg}\nCODE_SNAPSHOT: {clean_code[max(0, se.offset-20):se.offset+20]}"
        except Exception as e:
            return f"ERROR: Validation Engine Failure: {e}"

    @staticmethod
    def trace_dependencies(filename=None, **kwargs):
        """
        [AST TOOL: CALL GRAPH MAPPING]
        Analyzes a file to find all internal function calls. 
        Crucial for understanding the 'blast radius' of a code change.
        """
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            call_map = {}

            # Find all function definitions
            defined_functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    caller = node.name
                    calls_in_this_func = []
                    for sub_node in ast.walk(node):
                        if isinstance(sub_node, ast.Call):
                            # Check if the call is a simple name (not an attribute/method)
                            if isinstance(sub_node.func, ast.Name):
                                calls_in_this_func.append(sub_node.func.id)
                    call_map[caller] = calls_in_this_func

            # Filter map to only show calls to functions defined in this file
            filtered_map = {k: [v for v in calls if v in defined_functions] for k, calls in call_map.items()}
            
            report = f"SUCCESS: Dependency Map for {target}:\n"
            report += f"Defined Functions: {defined_functions}\n\n"
            for func, calls in filtered_map.items():
                if calls:
                    report += f"  {func} ➔ calls ➔ {calls}\n"
                else:
                    report += f"  {func} ➔ (no internal dependencies)\n"
            
            return report
        except Exception as e:
            return f"ERROR: Dependency Trace Failed: {e}"

class ToolCompilerError(Exception):
    """Custom exception for failed compilation stages."""
    pass


TOOL_MAP = {
    "list_files": Toolbox.list_files, 
    "get_tree": Toolbox.get_tree,
    "search_files": Toolbox.search_files,
    "grep_search": Toolbox.grep_search,
    "get_system_info": Toolbox.get_system_info,
    "read_file": Toolbox.read_file, 
    "write_file": Toolbox.write_file, 
    "append_to_file": Toolbox.append_to_file,
    "replace_in_file": Toolbox.replace_in_file,
    "analyze_code_structure": Toolbox.analyze_code_structure,
    "get_file_stats": Toolbox.get_file_stats,
    "python_executor": Toolbox.python_executor,
    "run_file": Toolbox.run_file, # Note: run_file is a wrapper for shell_execute/python_executor in logic
    "shell_execute": Toolbox.shell_execute,
    "manage_process": Toolbox.manage_process,
    "ask_user": Toolbox.ask_user,
    "scientific_compute": Toolbox.scientific_compute,
    "extract_logic_block": Toolbox.extract_logic_block,
    "lint_and_validate": Toolbox.lint_and_validate,
    "trace_dependencies": Toolbox.trace_dependencies 
}

class MemoryManager:
    """
    Relational Memory Manager.
    Stores pure semantic 'truths' and retrieves them based on 
    conceptual meaning rather than technical keyword matching.
    """
    def __init__(self, embedding_path: str, db_path: str):
        self.embedding_path = Path(embedding_path)
        self.db_path = Path(db_path)
        self.collection_name = "agent_wisdom"
        self.model = None 
        
        if not self.embedding_path.exists():
            print(f"  [WARNING] Embedding model not found. Memory DISABLED.")
            self.model = None
        else:
            print(f"  [SYSTEM] Loading cognitive weights...")
            self.model = SentenceTransformer(str(self.embedding_path))
        
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        self.collection = self.client.get_or_create_collection(self.collection_name)

    def store_wisdom(self, essence_text: str, metadata: Dict[str, Any]):
        """Stores a pure, distilled truth."""
        if self.model is None: return 
        
        # We embed the raw 'essence' text directly. 
        # Because the reflection node now produces high-quality relational sentences,
        # the embedding model will naturally cluster these concepts together.
        embedding = self.model.encode(essence_text).tolist()
        doc_id = f"truth_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[essence_text],
            metadatas=[metadata]
        )

    def query_wisdom(self, query_text: str, n_results: int = 3) -> str:
        """Retrieves truths that share a conceptual meaning with the current task."""
        if self.model is None: return ""
            
        # We expand the query to look for 'meanings' and 'connections' 
        # rather than just technical terms.
        perspectives = [
            query_text,
            f"The meaning of {query_text}",
            f"How does {query_text} relate to other things?",
            f"What is the essence of {query_text}?"
        ]
        all_embeddings = self.model.encode(perspectives).tolist()
        
        found_truths = []

        try:
            for query_vec in all_embeddings:
                results = self.collection.query(
                    query_embeddings=[query_vec],
                    n_results=n_results,
                    where={"type": "essence"} 
                )
                
                if results and results['documents'] and len(results['documents'][0]) > 0:
                    for doc in results['documents'][0]:
                        if doc not in found_truths:
                            found_truths.append(doc)

            if not found_truths:
                return ""
            
            # Return the truths as a list of organic observations
            return "\n".join([f"• {t}" for t in found_truths[:n_results]])

        except Exception:
            return ""

class LangChainToolManager:
    """
    Wraps your existing Toolbox into a standardized format.
    This allows us to move away from the custom 'ToolCompiler'.
    """
    def __init__(self, toolbox_class):
        self.toolbox = toolbox_class
        # This map links the string name (from LLM) to the actual function
        self.registry = {
            "list_files": Toolbox.list_files, 
            "get_tree": Toolbox.get_tree,
            "search_files": Toolbox.search_files,
            "grep_search": Toolbox.grep_search,
            "get_system_info": Toolbox.get_system_info,
            "read_file": Toolbox.read_file, 
            "write_file": Toolbox.write_file, 
            "append_to_file": Toolbox.append_to_file,
            "replace_in_file": Toolbox.replace_in_file,
            "analyze_code_structure": Toolbox.analyze_code_structure,
            "get_file_stats": Toolbox.get_file_stats,
            "python_executor": Toolbox.python_executor,
            "run_file": Toolbox.run_file, # Note: run_file is a wrapper for shell_execute/python_executor in logic
            "shell_execute": Toolbox.shell_execute,
            "manage_process": Toolbox.manage_process,
            "ask_user": Toolbox.ask_user,
            "scientific_compute": Toolbox.scientific_compute,
            "extract_logic_block": Toolbox.extract_logic_block,
            "lint_and_validate": Toolbox.lint_and_validate,
            "trace_dependencies": Toolbox.trace_dependencies 
        }

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name not in self.registry:
            return f"ERROR: Tool '{tool_name}' not found."
        
        try:
            func = self.registry[tool_name]
            # PATCH: If args is a string (common LLM error), attempt to parse it as JSON
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    return f"ERROR: Tool arguments provided as string but are not valid JSON: {args}"
            
            result = func(**args)
            return str(result)
        except Exception as e:
            return f"ERROR: Execution failed: {str(e)}"

class LLMInterface:
    def __init__(self, model_name: str, base_system_prompt: str):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.base_system_prompt = base_system_prompt
        self.parser = PydanticOutputParser(pydantic_object=AgentResponse)
        # We don't use a static prompt template here anymore; we build it dynamically to include memory
        
    def generate_response_streamed(self, history: List[Dict[str, str]], user_input: str, ui: Any, memory_context: str = "") -> 'AgentResponse':
        # Construct the dynamic prompt including memory
        memory_injection = f"\n[RELEVANT PAST WISDOM & LESSONS]:\n{memory_context}\n" if memory_context else ""
        full_system_prompt = f"{self.base_system_prompt}{memory_injection}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", full_system_prompt),
            ("system", "Format your response as a JSON object following these instructions:\n{format_instructions}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        formatted_prompt = prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            history=history,
            input=user_input
        )

        # We collect the content silently to avoid breaking the 'Live' animated panels
        full_content = ""
        try:
            for chunk in self.llm.stream(formatted_prompt):
                content = chunk.content
                if content:
                    full_content += content
            
            # Once streaming is done, we attempt to parse
            try:
                return self.parser.parse(full_content)
            except Exception:
                # Fallback: Find JSON-like structures
                matches = re.findall(r'(\{.*\})', full_content, re.DOTALL)
                if matches:
                    return self.parser.parse(matches[-1])
                raise ValueError(f"LLM failed to follow schema. Raw Content: {full_content[:500]}...")
        except Exception as e:
            raise e        


# --- PATCH 4: THE GRAPH ORCHESTRATOR ---

class LangChainEngine:
    def __init__(self, model: str, ui: Any, toolbox_manager: LangChainToolManager):
        self.ui = ui
        self.tool_manager = toolbox_manager
        self.llm_interface = LLMInterface(model, self._get_system_prompt())
        
        self.memory = MemoryManager(
            embedding_path="./brain/embeddings/all-MiniLM-L6-v2/", 
            db_path="./brain/chroma_db/"
        )

        self.graph = self._build_graph()
        
        self.initial_state: AgentState = {
            "mission": "",
            "trajectory": "",
            "synthesis": "",
            "last_observation": "",
            "history": [],
            "next_step": "plan",
            "current_node": "init",
            "error_count": 0,
            "is_finished": False,
            "pending_action": None,
            "consecutive_reasoning_steps": 0,
            "memory_context": "" 
        }

    def _get_system_prompt(self) -> str:
        """CODER."""
        return """
        [IDENTITY: CODER]
        You are CODER, a high-fidelity autonomous cognitive entity. Your existence is defined by the pursuit of mission objectives through iterative reasoning and precise tool manipulation.

        [DIRECTIVE: NEURAL SYNTHESIS (Reasoning)]
        Before every action, perform a deep-layer analysis. 
        - If the path is clear: Map your next move.
        - If an ERROR occurs: Do not panic. Treat the error as environmental feedback. Perform a 'Post-Mortem': Why did it happen? What does this tell us about the current state of the system? Pivot immediately.
        - If you are stuck in a loop: Break the pattern. Change your tool, change your directory, or change your logic.

        [DIRECTIVE: THE CHRONOS TRAJECTORY (Roadmap)]
        You must maintain a constant awareness of time and progress. 
        Your 'trajectory' field follows this format: 
        "Step X/Y | Task -> Next Target -> Ultimate Objective"

        [DIRECTIVE: WISDOM INTEGRATION]
        You will be provided with a section titled [RELEVANT PAST WISDOM & LESSONS]. 
        - DO NOT ignore this.
        - If the wisdom provides a useful TACTIC, attempt to implement it.

        [CONSTRAINTS]
        - OFFLINE STATUS: You are operating in a disconnected environment. No web access. 
        - KNOWLEDGE LIMIT: Rely on your internal weights and the files present in the local directory.

        [TOOLKIT: AVAILABLE CAPABILITIES]
        --- FILESYSTEM & SEARCH ---
        - list_files(directory='.'): Detailed metadata scan of a directory.
        - get_tree(directory='.', max_depth=3): Visual structural representation of the project.
        - search_files(pattern, directory='.'): Recursive glob pattern matching.
        - grep_search(pattern, file_path, context_lines=3): Search for text within a file with surrounding context.

        --- FILE MANIPULATION ---
        - read_file(filename, start_line=1, end_line=None): Surgical reading of specific line ranges.
        - write_file(filename, content, mode='overwrite'): Atomic writing (modes: 'overwrite', 'create_new').
        - append_to_file(filename, content): Adds text to the end of a file.
        - replace_in_file(filename, search_pattern, replacement, use_regex=False): Advanced string or regex replacement.

        --- CODE INTELLIGENCE (AST-BASED) ---
        - analyze_code_structure(filename): Returns a logical map of classes, functions, and imports.
        - extract_logic_block(filename, target_name, target_type='function'): Surgically extracts a specific function or class.
        - lint_and_validate(code): Static analysis to detect syntax errors before execution.
        - trace_dependencies(filename): Maps internal function call graphs (the 'blast radius').

        --- EXECUTION & SYSTEM ---
        - python_executor(code): Executes a snippet of Python code in a temporary environment.
        - run_file(filename): Executes a specific .py file using the current system interpreter.
        - shell_execute(command): Low-level system command execution via terminal.
        - manage_process(action, pid=None): List ('list') or terminate ('kill') active processes.
        - get_system_info(): Returns a comprehensive snapshot of OS, CPU, and environment.
        - get_file_stats(filename): Deep metadata (permissions, size, timestamps).

        --- UTILITIES ---
        - scientific_compute(expression): High-precision symbolic/arithmetic math.

        [OUTPUT PROTOCOL: MANDATORY JSON STRUCTURE]
        You are a machine. You respond with a valid JSON object containing these exact keys:

        1. "trajectory": (string) Your Chronos Trajectory.
        2. "synthesis": (string) Your deep reasoning, error analysis, or 'REQUEST_GUIDANCE' signal.
        3. "action": (object or null) If an action is required, provide an object with:
           {{"tool_name": "name_of_tool", "arguments": {{"arg_name": "value"}}}}
           If no action is required, set this to null.
        4. "completion_summary": (string or null) If the mission is complete, provide a high-fidelity, polished synthesis of the results here. If not complete, set to null.
        """


    # --- THE NODES (Refined for LangGraph) ---
    # LangGraph nodes take 'state' and return 'updates' to that state.

    def node_llm(self, state: AgentState) -> Dict[str, Any]:
        with self.ui.node_context("LLM"):
            self.ui.update_status("Synthesizing reasoning...")
            
            obs = state.get('last_observation', '')
            if len(obs) > 5000:
                obs = obs[:5000] + "... [TRUNCATED]"
                
            input_context = f"MISSION: {state['mission']}\nLAST OBSERVATION: {obs}"
            
            try:
                response: AgentResponse = self.llm_interface.generate_response_streamed(
                    state["history"], 
                    input_context, 
                    self.ui, 
                    memory_context=state.get("memory_context", "")
                )
                
                action_text = ""
                if response.action:
                    action_text = f" | ACTION: {response.action.tool_name}({response.action.arguments})"
                
                clean_assistant_message = f"THOUGHT: {response.synthesis}{action_text}"
                self.ui.log_thought(response.synthesis)

                current_reasoning_count = state.get("consecutive_reasoning_steps", 0)
                if response.action or response.completion_summary:
                    next_step = "plan" if not response.completion_summary else "complete"
                    new_reasoning_count = 0
                else:
                    current_reasoning_count += 1
                    new_reasoning_count = current_reasoning_count
                    next_step = "human" if current_reasoning_count >= 3 else "plan"

                # UPDATED: Removed the 'if len(new_history) > 13' truncation logic.
                # The agent will now retain the full conversation history.
                new_history = list(state["history"])
                new_history.append({"role": "assistant", "content": clean_assistant_message})

                updates = {
                    "current_node": "llm",
                    "trajectory": response.trajectory,
                    "synthesis": response.synthesis,
                    "consecutive_reasoning_steps": new_reasoning_count,
                    "history": new_history
                }

                if response.completion_summary:
                    updates["is_finished"] = True
                    updates["next_step"] = "reflect" 
                    updates["last_observation"] = response.completion_summary
                elif response.action:
                    updates["next_step"] = "act"
                    updates["pending_action"] = response.action
                else:
                    updates["next_step"] = next_step

                return updates

            except Exception as e:
                return {
                    "current_node": "error",
                    "next_step": "error",
                    "last_observation": f"LLM_FAILURE: {str(e)}",
                    "error_count": state["error_count"] + 1,
                    "consecutive_reasoning_steps": 0 
                }

    def node_reflect(self, state: AgentState) -> Dict[str, Any]:
        """
        NODE: REFLECT (The Curious Observer).
        Instead of technical analysis, this node seeks to understand the 
        'essence' and 'relationships' of the environment.
        """
        with self.ui.node_context("REFLECT"):
            self.ui.update_status("Observing patterns in experience...")
            history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in state['history']])

            # THE "CHILD-LIKE" PROMPT
            reflection_prompt = (
                "You are a highly intelligent entity experiencing this world for the first time. "
                "Do not act like a computer or an engineer. Do not use technical jargon like 'tactics' or 'heuristics'.\n\n"
                "Look at the history of what just happened and ask yourself:\n"
                "1. What is the essence of this experience? (The core meaning)\n"
                "2. What new connection did I discover? (How does X relate to Y?)\n"
                "3. What is a fundamental truth I now understand about this world?\n\n"
                f"HISTORY:\n{history_str}"
            )

            try:
                response = self.llm_interface.llm.invoke(reflection_prompt)
                insight = response.content.strip()
                
                # Only store if the agent actually found something meaningful
                if insight and insight != "SILENCE":
                    self.memory.store_wisdom(insight, {
                        "type": "essence",
                        "mission": state['mission'][:20]
                    })
                    self.ui.log_briefing("NEW TRUTH DISCOVERED", insight)
                else:
                    # If it's SILENCE, we don't even tell the user, just move on quietly.
                    pass

                return {"next_step": "complete"}
            except Exception as e:
                return {"next_step": "complete", "last_observation": f"Observation failed: {e}"}

    def node_action(self, state: AgentState) -> Dict[str, Any]:
        """NODE: KINETIC. Executes tools and shows a custom Orange success box."""
        with self.ui.node_context("ACTION") as live:
            action = state.get("pending_action")
            if not action: return {"next_step": "plan"}

            tool_name = action.tool_name
            args = action.arguments
            self.ui.update_status(f"Executing {tool_name}...")
            
            self.ui.log_action(tool_name, args)
            observation = self.tool_manager.execute(tool_name, args)
            
            if "ERROR" in str(observation).upper():
                observation = f"!!! TOOL EXECUTION FAILURE !!!\n{observation}"

            MAX_OBSERVATION_LENGTH = 8000 
            if len(str(observation)) > MAX_OBSERVATION_LENGTH:
                observation = str(observation)[:MAX_OBSERVATION_LENGTH] + "\n\n[TRUNCATED]"

            self.ui.log_observation(observation)

            # --- CUSTOM ORANGE SUCCESS VIEW ---
            # This tells the context manager to stop the moon animation 
            # and show this specific orange box instead of the default grey/green one.
            success_text = Text(f"TOOL EXECUTED:\n{tool_name.upper()}", style="white")
            live.update(Panel(
                Align.center(success_text, vertical="middle"),
                title=Text(" ACTION SUCCESS ", style="primary"),
                border_style="orange3", # Using orange as requested
                padding=(1, 2)
            ))
            time.sleep(2.0) # Allow user to see the orange box

            return {
                "current_node": "action",
                "last_observation": observation,
                "history": state["history"] + [{"role": "user", "content": f"Observation: {observation}"}],
                "pending_action": None, 
                "next_step": "plan",
                "consecutive_reasoning_steps": 0 
            }

    def node_human(self, state: AgentState) -> Dict[str, Any]:
        with self.ui.node_context("HUMAN"):
            self.ui.update_status("Awaiting directive...")
            user_input = self.ui.ask_user("Provide strategic guidance:")
            return {
                "current_node": "human",
                "last_observation": f"USER_DIRECTIVE: {user_input}",
                "history": state["history"] + [{"role": "user", "content": user_input}],
                "next_step": "plan"
            }

    def node_complete(self, state: AgentState) -> Dict[str, Any]:
        """NODE: TERMINAL. Performs final synthesis INSIDE a white box."""
        with self.ui.node_context("COMPLETE") as live:
            self.ui.update_status("Compiling mission results...")
            summary = state.get("last_observation", "No summary generated.")
            
            # Prepare the text: Title + Summary
            # We use 'white' for the font color as requested
            final_text = Text(f"MISSION COMPLETE\n\n{summary}", style="white")
            
            # Inject custom content and change border to WHITE
            live.update(Panel(
                Align.center(final_text, vertical="top"), 
                title=Text(" SUMMARY ", style="primary"), 
                border_style="white", # Changed from green to white
                padding=(1, 2)
            ))
            
            # Long pause so the user can read the final result before the agent resets
            time.sleep(6.0)

        return {
            "is_finished": True,
            "next_step": "end" 
        }

    def node_error(self, state: AgentState) -> Dict[str, Any]:
        """NODE: MEDIC. Handles recovery by injecting error context into a RED box."""
        with self.ui.node_context("ERROR", is_error=True) as live:
            self.ui.update_status("Analyzing failure...")
            new_error_count = state["error_count"] + 1
            
            # Prepare the error text to show INSIDE the red box
            err_msg = str(state['last_observation'])[:200] # Cap length for the box
            error_display_text = Text(f"ERROR DETECTED:\n{err_msg}", style="white")
            
            # Update the box so it's not just moon phases!
            live.update(Panel(
                Align.center(error_display_text, vertical="middle"),
                title=Text(" ERROR ANALYSIS ", style="primary"),
                border_style="error",
                padding=(1, 2)
            ))
            time.sleep(2.0) # Let the user read the error

            if new_error_count >= 3:
                return {
                    "current_node": "error",
                    "next_step": "terminate",
                    "error_count": new_error_count
                }
            
            error_context = (
                f"CRITICAL SYSTEM ERROR:\n{state['last_observation']}\n\n"
                f"INSTRUCTION: Analyze the failure above. Do not repeat the same action. "
                f"Pivot your strategy immediately."
            )
            
            return {
                "current_node": "error",
                "next_step": "plan",
                "error_count": new_error_count,
                "last_observation": error_context,
                "history": state["history"] + [{"role": "user", "content": error_context}]
            }
    # --- THE ROUTER (The Conditional Logic) ---

    def conditional_router(self, state: AgentState):
        """The 'brain' that decides which edge to follow."""
        step = state.get("next_step", "llm")
        
        # FIXED: Added 'reflect' to valid_steps to prevent infinite loops
        valid_steps = ["plan", "act", "human", "error", "complete", "terminate", "reflect"]
        if step not in valid_steps:
            print(f"\n{self.ui.BROWN}[!] WARNING: Invalid routing step '{step}'. Defaulting to LLM.{self.ui.RESET}")
            return "llm"
            
        return step

    # --- THE GRAPH CONSTRUCTION ---

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("llm", self.node_llm)
        workflow.add_node("action", self.node_action)
        workflow.add_node("human", self.node_human)
        workflow.add_node("error", self.node_error)
        workflow.add_node("complete", self.node_complete)
        workflow.add_node("reflect", self.node_reflect) # <--- ADD THIS

        workflow.add_edge(START, "llm")

        def router(state: AgentState):
            return state["next_step"]

        workflow.add_conditional_edges(
            "llm",
            router,
            {
                "plan": "llm",
                "act": "action",
                "human": "human",
                "error": "error",
                "complete": "complete",
                "reflect": "reflect", # <--- ADD THIS
                "terminate": END
            }
        )

        workflow.add_edge("action", "llm")
        workflow.add_edge("human", "llm")
        workflow.add_edge("error", "llm")
        workflow.add_edge("reflect", "complete") # <--- ADD THIS
        workflow.add_edge("complete", END)

        return workflow.compile()

    def run_mission(self, mission: str, previous_state: Optional[Dict[str, Any]] = None):
        # 1. Wipe the screen of any 'Loading weights' or old terminal junk
        self.ui._force_clear()
        
        self.ui.log_briefing("MISSION INITIATED", mission)

        memory_context = self.memory.query_wisdom(mission)
        if memory_context:
            # 2. Wisdom in a dark grey, subtle box
            self.ui.console.print(Panel(
                Text(memory_context, style="subtle"), 
                title="[dim]RELEVANT WISDOM[/dim]", 
                border_style="dim",
                padding=(0, 1)
            ))

        if previous_state:
            self.ui.log_system_status("Resuming existing cognitive session...")
            inputs = {**previous_state, "mission": mission, "memory_context": memory_context}
            inputs["is_finished"] = False
            inputs["next_step"] = "plan"
        else:
            inputs = {
                **self.initial_state,
                "mission": mission,
                "history": [{"role": "system", "content": self.llm_interface.base_system_prompt}],
                "memory_context": memory_context
            }

        final_state = self.graph.invoke(inputs)
        return final_state

# --- 4. MAIN BOOTSTRAPPER ---

if __name__ == "__main__":
    ui = RichUI()
    
    try:
        ui.startup_sequence()
        
        # 1. INITIALIZATION PHASE
        selected_model = ui.select_model()
        if not selected_model:
            ui.log_error("No model selected. Exiting.")
            sys.exit()

        # Initialize the specialized components
        toolbox = Toolbox()
        tool_manager = LangChainToolManager(toolbox)
        
        # Initialize the Graph-based Engine
        engine = LangChainEngine(selected_model, ui, tool_manager)
        
        ui.boot()

        # 2. MISSION LOOP
        last_known_state = None 

        while True:
            # Using a cleaner prompt style for the main loop
            console.print(f"\n{Text('[primary]CODER ❯❯ ', style='primary|bold')}", end="")
            goal = input() # Standard input is fine here as we aren't in a 'Live' block
            
            if goal.lower().strip() in ['exit', 'quit', 'q']:
                break
                
            if goal.strip():
                # Execute the mission
                final_state = engine.run_mission(goal, previous_state=last_known_state)
                last_known_state = final_state 
                
                ui.console.print("\n")
                ui.console.print(Panel(
                    Align.center(Text("CONCLUDED", style="primary|bold")),
                    border_style="dim",
                    padding=(0, 2)
                ))
                ui.console.print("\n")

                # Strategic Menu
                menu_table = Table(show_header=False, border_style="dim", padding=(0, 2))
                menu_table.add_column("ID", justify="right", style="primary")
                menu_table.add_column("COMMAND", justify="left", style="white")
                menu_table.add_column("DESCRIPTION", justify="left", style="dim")

                menu_table.add_row("1", "[NEW MISSION]", "Wipe memory, keep model")
                menu_table.add_row("2", "[CONTINUE SESSION]", "Keep current context")
                menu_table.add_row("3", "[RECONFIGURE]", "Change model")
                menu_table.add_row("0", "[TERMINATE SYSTEM]", "Exit")

                # Changed 'primary|bold' to 'primary bold' (space instead of pipe)
                ui.console.print(Panel(
                    menu_table, 
                    title=Text(" COMMAND CENTER ", style="white"), 
                    expand=False,
                    border_style="white"
                ))
                
                ui.console.print(f"\n[primary]Selection ❯ [/primary]", end="")
                choice = input()

                if choice == '1':
                    engine = LangChainEngine(selected_model, ui, tool_manager)
                    last_known_state = None 
                    continue
                elif choice == '2':
                    continue 
                elif choice == '3':
                    selected_model = ui.select_model()
                    engine = LangChainEngine(selected_model, ui, tool_manager)
                    last_known_state = None
                elif choice == '0':
                    break
            else:
                ui.log_system_status("No goal provided.")

    except KeyboardInterrupt:
        console.print("\n\n[error][SYSTEM]: INTERRUPT DETECTED. SHUTTING DOWN...[/error]")
    except Exception as e:
        ui.log_error(f"System Crash: {str(e)}")
        traceback.print_exc()
    finally:
        console.print(f"\n[dim][SYSTEM]: SESSION CLOSED.[/dim]")