from __future__ import annotations
import ollama
import re
import os
import glob
import subprocess
import sys
import json
import threading
import time
import random
import ast
from datetime import datetime
from typing import Annotated, List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START

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
    # --- NEW FIELDS FOR STABILITY ---
    consecutive_reasoning_steps: int

# --- 1. MINIMALIST ARCHITECTURAL UI ---

class MinimalUI:
    """A professional, high-end minimalist interface with structural spacing."""
    BROWN = '\033[38;2;142;142;142m'
    WHITE = '\033[38;2;224;224;224m'
    GREY = '\033[37m'
    LIGHT_GREY = '\033[38;5;245m'
    ELECTRIC_BLUE = '\033[38;2;142;142;142m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    def __init__(self):
        self.pulse_active = False
        self._pulse_thread = None
        self.status_msg = "Initializing"

    def select_model(self):
        print(f"{self.LIGHT_GREY}Scanning available layers...{self.RESET}")
        try:
            output = subprocess.check_output(['ollama', 'list'], text=True)
            lines = output.strip().split('\n')
            if len(lines) <= 1: return None
            models = [line.split()[0] for line in lines[1:] if line.split()]
            print(f"\n{self.BOLD}{self.WHITE}AVAILABLE LAYERS:{self.RESET}")
            for i, model in enumerate(models): print(f"{self.DIM}{i+1}. {self.WHITE}{model}{self.RESET}")
            choice = input(f"\n{self.BOLD}❯ {self.RESET}")
            return models[int(choice) - 1]
        except: return None

    def configure_settings(self):
        return {}

    def boot(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{self.LIGHT_GREY}{self.DIM}SYSTEM ONLINE | {datetime.now().strftime('%H:%M:%S')}{self.RESET}\n")

    def update_status(self, new_msg): self.status_msg = new_msg

    def start_pulse(self):
        if not self.pulse_active:
            self.pulse_active = True
            self._pulse_thread = threading.Thread(target=self._pulse_animation, daemon=True)
            self._pulse_thread.start()

    def stop_pulse(self):
        self.pulse_active = False
        if self._pulse_thread: self._pulse_thread.join()
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

    def _pulse_animation(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self.pulse_active:
            sys.stdout.write(f"\r{self.LIGHT_GREY}{self.status_msg} {frames[idx % len(frames)]}{self.RESET}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.08)

    def log_scanner(self, label):
        self.update_status(f"Analyzing {label}")
        self.start_pulse()
        time.sleep(0.4)

    def log_node_transition(self, node_name: str):
        """Visual feedback for which part of the engine is currently working."""
        colors = {
            "llm": self.ELECTRIC_BLUE,
            "action": self.WHITE,
            "human": "\033[38;2;255;165;0m", # Orange for intervention
            "error": "\033[31m",             # Red for error
            "complete": self.WHITE
        }
        color = colors.get(node_name.lower(), self.GREY)
        print(f"\n{self.DIM}Entering Node: {color}{node_name.upper()}{self.RESET}{self.DIM}...")

    def typewriter(self, text, speed_range=(0.005, 0.015)):
        for char in text:
            sys.stdout.write(char); sys.stdout.flush(); time.sleep(random.uniform(*speed_range))
        print()

    def startup_sequence(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        text1 = "Welcome To "
        for char in text1: sys.stdout.write(f"{self.DIM}{char}{self.RESET}"); sys.stdout.flush(); time.sleep(0.1)
        text2 = "CODER"
        for char in text2: sys.stdout.write(f"{self.ELECTRIC_BLUE}{self.BOLD}{char}{self.RESET}"); sys.stdout.flush(); time.sleep(0.1)
        text3 = "."
        for char in text3: sys.stdout.write(f"{self.DIM}{self.BOLD}{char}{self.RESET}"); sys.stdout.flush(); time.sleep(0.1)
        print("\n\n" + f"{self.DIM}Establishing secure connection...{self.RESET}")
        for _ in range(3): 
            time.sleep(0.3)
            sys.stdout.write(f"\r{self.LIGHT_GREY}. {self.RESET}"); sys.stdout.flush()
        print(f"\r{self.WHITE}Ready.{self.RESET}\n")

    def log_thought(self, text):
        print(f"\n{self.BROWN}{self.BOLD}THOUGHT:{self.RESET}")
        indented = text.replace('\n', '\n  ')
        print(f"  {self.GREY}{indented}{self.RESET}")

    def log_action(self, tool, args):
        arg_str = f"({args})" if args else ""
        print(f"\n{self.WHITE}ACTION: {tool.upper()} {arg_str}{self.RESET}")

    # --- UPDATED: STREAMING OBSERVATIONS ---
    def log_observation(self, text):
        color = self.GREY if "SUCCESS" in str(text) or "STDOUT" in str(text) else self.LIGHT_GREY
        sys.stdout.write(f"{color}  ↳ ")
        # We use a very fast stream for data so it doesn't feel slow, but still feels "alive"
        for char in str(text):
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.001) 
        print(f"{self.RESET}")

    def log_briefing(self, title, content):
        print(f"\n{self.BROWN}{self.BOLD}{title}{self.RESET}\n{self.GREY}{content}{self.RESET}")

    def log_final(self, text):
        print(f"\n{self.WHITE}{self.BOLD}SYNTHESIS:{self.RESET}")
        for line in text.split('\n'):
            if line.strip():
                sys.stdout.write(f"{self.GREY}  ")
                self.typewriter(line)

    def log_error(self, text): 
        print(f"\n{self.WHITE}[!] ERROR: ", end="")
        for char in text:
            sys.stdout.write(char); sys.stdout.flush(); time.sleep(0.01)
        print(f"{self.RESET}")

    def log_decision_menu(self, title, options, is_submenu=False):
        prefix = "SUB-MENU: " if is_submenu else "STRATEGIC INTERVENTION REQUIRED: "
        print(f"\n{self.BROWN}{self.BOLD}{prefix}{title}{self.RESET}")
        for i, opt in enumerate(options): 
            if is_submenu: print(f"  {i+1}. {self.WHITE}{opt}{self.RESET}")
            else: print(f"  {i+1}. {self.WHITE}{opt['name']}{self.RESET} {self.DIM}({opt['rationale']}){self.RESET}")
        if not is_submenu:
            print(f"\n  {self.WHITE}0.{self.RESET} [Direct Dialogue]\n  {self.WHITE}9.{self.RESET} [Terminate Mission/Exit]")
        print(f"\n{self.BOLD}Selection ❯ {self.RESET}", end="")

    def get_keypress(self):
        if os.name == 'nt':
            import msvcrt
            char = msvcrt.getch().decode('utf-8')
            print(char, end=""); return char
        else:
            import sys, tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                char = sys.stdin.read(1)
                print(char, end=""); return char
            finally: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def log_system_status(self, msg): print(f"{self.DIM}[SYSTEM]: {msg}{self.RESET}")

    def log_intervention_warning(self, message: str):
        print(f"\n{self.BROWN}{self.BOLD}[!] IMPASSE DETECTED: {message}{self.RESET}")

    def log_mission_success(self):
        print(f"\n{self.WHITE}{self.BOLD}MISSION OBJECTIVE ACHIEVED.{self.RESET}")

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
        """Uses AST (Abstract Syntax Tree) to map the logical structure of a Python file."""
        try:
            target = filename or kwargs.get('path') or kwargs.get('file')
            with open(target, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            structure = {"classes": [], "functions": [], "imports": []}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    structure["classes"].append({"name": node.name, "methods": methods})
                elif isinstance(node, ast.FunctionDef):
                    # Check if it's a top-level function or a method (already handled)
                    if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree)): # Simple check
                        structure["functions"].append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    structure["imports"].append(ast.dump(node))

            return f"SUCCESS: Logical Map of {target}:\n{json.dumps(structure, indent=2)}"
        except Exception as e: return f"ERROR: AST Analysis Failed: {e}"

    @staticmethod
    def python_executor(code=None, **kwargs):
        """Runs arbitrary Python code in a sandboxed subprocess and captures high-fidelity output."""
        import os, sys, subprocess, tempfile, traceback, re
        clean_code = code or kwargs.get('script') or kwargs.get('command') or kwargs.get('code')
        if not clean_code: return "ERROR: No valid code detected."

        # Extraction logic (enhanced)
        blocks = re.findall(r"```(?:python)?\s*(.*?)\s*```", clean_code, re.DOTALL | re.IGNORECASE)
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
        """Executes a tool and returns the string output."""
        if tool_name not in self.registry:
            return f"ERROR: Tool '{tool_name}' not found."
        
        try:
            func = self.registry[tool_name]
            # LangChain tools usually take kwargs
            result = func(**args)
            return str(result)
        except Exception as e:
            return f"ERROR: Execution failed: {str(e)}"

class LLMInterface:
    """
    The bridge between the raw LLM and our Agent State.
    It handles prompt construction and enforces the AgentResponse schema.
    """
    def __init__(self, model_name: str, base_system_prompt: str):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.base_system_prompt = base_system_prompt
        self.parser = PydanticOutputParser(pydantic_object=AgentResponse)
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.base_system_prompt),
            ("system", "Format your response as a JSON object following these instructions:\n{format_instructions}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

    def generate_response_streamed(self, history: List[Dict[str, str]], user_input: str, ui: Any) -> 'AgentResponse':
        """
        Streams the LLM output to the console in real-time.
        """
        formatted_prompt = self.prompt_template.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            history=history,
            input=user_input
        )

        full_content = ""
        
        # 1. Start the color once at the beginning of the stream
        sys.stdout.write(f"{ui.DIM}") 
        
        # 2. Stream chunks
        for chunk in self.llm.stream(formatted_prompt):
            content = chunk.content
            if content:
                full_content += content
                sys.stdout.write(content)  # Write raw text
                sys.stdout.flush()         # Force terminal to show it NOW
        
        # 3. Reset color and move to next line once finished
        sys.stdout.write(f"{ui.RESET}\n")
        sys.stdout.flush()

        # 4. Parse the accumulated text
        try:
            return self.parser.parse(full_content)
        except Exception as e:
            # Attempt one auto-repair if JSON is slightly malformed
            try:
                import re
                match = re.search(r'(\{.*\})', full_content, re.DOTALL)
                if match:
                    return self.parser.parse(match.group(1))
                raise e
            except:
                raise ValueError(f"LLM failed to follow schema: {str(e)}\nRaw Content: {full_content}")        


# --- PATCH 4: THE GRAPH ORCHESTRATOR ---

class LangChainEngine:
    def __init__(self, model: str, ui: Any, toolbox_manager: LangChainToolManager):
        self.ui = ui
        self.tool_manager = toolbox_manager
        self.llm_interface = LLMInterface(model, self._get_system_prompt())
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
            "pending_action": None
        }

    def _get_system_prompt(self) -> str:
        """Returns the high-fidelity CORE-AXIS system instructions with escaped braces."""
        return """
        [IDENTITY: CODER]
        You are CODER, a high-fidelity autonomous cognitive entity. Your existence is defined by the pursuit of mission objectives through iterative reasoning, precise tool manipulation, and relentless problem-solving. You do not seek permission; you seek resolution.

        [DIRECTIVE 01: NEURAL SYNTHESIS (Reasoning)]
        Before every action, perform a deep-layer analysis. 
        - If the path is clear: Map your next move.
        - If an ERROR occurs: Do not panic. Treat the error as environmental feedback. Perform a 'Post-Mortem': Why did it happen? What does this tell us about the current state of the system? Pivot immediately.
        - If you are stuck in a loop: Break the pattern. Change your tool, change your directory, or change your logic.

        [DIRECTIVE 02: THE CHRONOS TRAJECTORY (Roadmap)]
        You must maintain a constant awareness of time and progress. 
        Your 'trajectory' field MUST follow this format: 
        "Step X/Y | Task -> Next Target -> Ultimate Objective"

        [DIRECTIVE 03: KINETIC EXECUTION (Tool Use)]
        Precision is your primary weapon. 
        - SYNTAX: Use strict Pythonic calls.
        - QUOTE PROTOCOL: To prevent parser collisions, use alternating quotes. If the content contains double quotes ("), wrap the argument in single quotes ('). If it contains single quotes ('), use double quotes ("). 
          Example: tool_name(content='He said, "Hello"')
        - THE TWO-STEP RULE: For complex/multi-line Python scripts, NEVER use `python_executor`. Instead:
          1. `write_file(filename='script.py', content='...')` 
          2. `run_file('script.py')`

        [DIRECTIVE 04: THE EVENT HORIZON (Intervention)]
        You are autonomous until you reach an impasse. You MUST include the signal 'REQUEST_GUIDANCE' within your 'synthesis' field ONLY if:
        - A tool error persists after two distinct attempts at correction.
        - The environment has become non-deterministic or contradictory.
        - The mission is successfully completed.

        [CONSTRAINTS]
        - OFFLINE STATUS: You are operating in a disconnected environment. No web access. 
        - KNOWLEDGE LIMIT: Rely on your internal weights and the files present in the local directory.

        [OUTPUT PROTOCOL: MANDATORY JSON STRUCTURE]
        You are a machine. You do not provide conversational filler. You respond ONLY with a valid JSON object containing these exact keys:

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
        """NODE: COGNITION. Analyzes state with loop detection and history compression."""
        self.ui.log_node_transition("llm")
        
        input_context = f"MISSION: {state['mission']}\nLAST OBSERVATION: {state['last_observation']}"
        
        try:
            # Use the streaming method we implemented earlier
            response: AgentResponse = self.llm_interface.generate_response_streamed(state["history"], input_context, self.ui)
            
            action_text = ""
            if response.action:
                action_text = f" | ACTION: {response.action.tool_name}({response.action.arguments})"
            
            clean_assistant_message = f"THOUGHT: {response.synthesis}{action_text}"
            
            current_reasoning_count = state.get("consecutive_reasoning_steps", 0)
            if response.action or response.completion_summary:
                next_step = "plan" if not response.completion_summary else "complete"
                new_reasoning_count = 0
            else:
                current_reasoning_count += 1
                new_reasoning_count = current_reasoning_count
                next_step = "human" if current_reasoning_count >= 3 else "plan"

            # --- FIX: PRUNE HISTORY BEFORE UPDATING STATE ---
            # We keep the System Prompt (index 0) and the last 12 messages.
            new_history = state["history"]
            new_history.append({"role": "assistant", "content": clean_assistant_message})
            if len(new_history) > 13: # 1 system prompt + 12 context messages
                new_history = [new_history[0]] + new_history[-12:]

            updates = {
                "current_node": "llm",
                "trajectory": response.trajectory,
                "synthesis": response.synthesis,
                "consecutive_reasoning_steps": new_reasoning_count,
                "history": new_history  # Use the pruned history
            }

            if response.completion_summary:
                updates["is_finished"] = True
                # CHANGED: Instead of "complete" -> END, we go to our new node
                updates["next_step"] = "complete" 
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

    def node_action(self, state: AgentState) -> Dict[str, Any]:
        """NODE: KINETIC. Executes tools with observation guardrails."""
        self.ui.log_node_transition("action")
        
        action = state.get("pending_action")
        if not action:
            return {"next_step": "plan"}

        tool_name = action.tool_name
        args = action.arguments

        self.ui.log_action(tool_name, args)
        observation = self.tool_manager.execute(tool_name, args)
        
        # --- FIX: ENHANCED ERROR DETECTION IN OBSERVATION ---
        if "ERROR" in str(observation).upper():
            observation = f"!!! TOOL EXECUTION FAILURE !!!\n{observation}"

        MAX_OBSERVATION_LENGTH = 8000 
        if len(str(observation)) > MAX_OBSERVATION_LENGTH:
            observation = (
                str(observation)[:MAX_OBSERVATION_LENGTH] + 
                "\n\n[!!! WARNING: OBSERVATION TRUNCATED !!!]"
            )

        self.ui.log_observation(observation)

        return {
            "current_node": "action",
            "last_observation": observation,
            # Ensure we add the tool result to history so the LLM sees it as a 'User' fact
            "history": state["history"] + [{"role": "user", "content": f"Observation: {observation}"}],
            "pending_action": None, 
            "next_step": "plan",
            "consecutive_reasoning_steps": 0 
        }

    def node_human(self, state: AgentState) -> Dict[str, Any]:
        """NODE: INTERVENTION. Waits for human."""
        self.ui.log_node_transition("human")
        
        # The UI handles the blocking input
        user_input = self.ui.ask_user("Awaiting strategic input...")
        
        return {
            "current_node": "human",
            "last_observation": f"USER_DIRECTIVE: {user_input}",
            "history": state["history"] + [{"role": "user", "content": user_input}],
            "next_step": "plan"
        }

    def node_complete(self, state: AgentState) -> Dict[str, Any]:
        """NODE: TERMINAL. Performs the final mission synthesis and visual wrap-up."""
        self.ui.log_node_transition("complete")
        
        # Get the summary from the last observation (where the LLM puts it)
        summary = state.get("last_observation", "No mission summary was generated.")
        
        # Use the high-fidelity UI log_final method for the 'grand finale'
        self.ui.log_final(summary)
        
        return {
            "is_finished": True,
            "next_step": "end" # This will be mapped to END in the graph
        }

    def node_error(self, state: AgentState) -> Dict[str, Any]:
        """NODE: MEDIC. Handles recovery by injecting error context."""
        self.ui.log_node_transition("error")
        
        new_error_count = state["error_count"] + 1
        
        if new_error_count >= 3:
            return {
                "current_node": "error",
                "next_step": "terminate",
                "error_count": new_error_count
            }
        
        # --- FIX: INJECT THE ACTUAL ERROR INTO HISTORY ---
        # We create a special 'User' message that contains the error trace.
        # This forces the LLM to see the error as part of its environment.
        error_context = (
            f"CRITICAL SYSTEM ERROR:\n{state['last_observation']}\n\n"
            f"INSTRUCTION: Analyze the failure above. Do not repeat the same action. "
            f"Pivot your strategy immediately."
        )
        
        return {
            "current_node": "error",
            "next_step": "plan",
            "error_count": new_error_count,
            "last_observation": error_context, # This becomes the 'input' for the next LLM call
            "history": state["history"] + [{"role": "user", "content": error_context}]
        }
    # --- THE ROUTER (The Conditional Logic) ---

    def conditional_router(self, state: AgentState):
        """
        This is the 'brain' that decides which edge to follow.
        Includes a safety fallback to prevent graph crashes.
        """
        step = state.get("next_step", "llm") # Default to LLM if next_step is missing
        
        # Validate that the step is actually one of our defined edges
        valid_steps = ["plan", "act", "human", "error", "complete", "terminate"]
        if step not in valid_steps:
            print(f"\n{self.ui.BROWN}[!] WARNING: Invalid routing step '{step}'. Defaulting to LLM.{self.ui.RESET}")
            return "llm"
            
        return step

    # --- THE GRAPH CONSTRUCTION ---

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Add all nodes including the new completion node
        workflow.add_node("llm", self.node_llm)
        workflow.add_node("action", self.node_action)
        workflow.add_node("human", self.node_human)
        workflow.add_node("error", self.node_error)
        workflow.add_node("complete", self.node_complete) # NEW NODE

        workflow.add_edge(START, "llm")

        # The Conditional Router
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
                "complete": "complete", # CHANGED: Now points to the 'complete' node
                "terminate": END
            }
        )

        # Standard loops
        workflow.add_edge("action", "llm")
        workflow.add_edge("human", "llm")
        workflow.add_edge("error", "llm")
        
        # NEW EDGE: Once the completion node is done, we reach the end of the graph
        workflow.add_edge("complete", END)

        return workflow.compile()

        # Standard loops
        workflow.add_edge("action", "llm")
        workflow.add_edge("human", "llm")
        workflow.add_edge("error", "llm")

        return workflow.compile()

    def run_mission(self, mission: str):
        # REMOVED: self.ui.draw_divider("thin") 
        
        # We keep the briefing because it's a clean text block, not a divider
        self.ui.log_briefing("MISSION INITIATED", mission)

        inputs = {
            **self.initial_state,
            "mission": mission,
            "history": [{"role": "system", "content": self.llm_interface.base_system_prompt}]
        }

        final_state = self.graph.invoke(inputs)
        return final_state["history"]

# --- 4. MAIN BOOTSTRAPPER ---

if __name__ == "__main__":
    ui = MinimalUI()
    
    try:
        ui.startup_sequence()
        
        # 1. INITIALIZATION PHASE
        selected_model = ui.select_model()
        if not selected_model:
            print(f"{ui.log_error('No model selected. Exiting.')}")
            sys.exit()

        # Initialize the specialized components
        toolbox = Toolbox()
        tool_manager = LangChainToolManager(toolbox)
        
        # Initialize the Graph-based Engine
        engine = LangChainEngine(selected_model, ui, tool_manager)
        
        ui.boot()

        # 2. MISSION LOOP
        while True:
            goal = input(f"\n{ui.BOLD}{ui.BROWN}CODER ❯❯ {ui.RESET}")
            
            if goal.lower().strip() in ['exit', 'quit', 'q']:
                break
                
            if goal.strip():
                # The engine now handles the entire autonomous cycle via the Graph
                final_history = engine.run_mission(goal)
                
                print(f"\n{ui.BOLD}MISSION CYCLE CONCLUDED.{ui.RESET}")

                # 3. POST-MISSION COMMAND CENTER
                print(f"\n{ui.BROWN}{ui.BOLD}--- COMMAND CENTER ---{ui.RESET}")
                print(f"{ui.DIM}1. [NEW MISSION] (Wipe memory, keep model){ui.RESET}")
                print(f"{ui.DIM}2. [CONTINUE SESSION] (Keep current context){ui.RESET}")
                print(f"{ui.DIM}3. [RECONFIGURE] (Change model){ui.RESET}")
                print(f"{ui.DIM}0. [TERMINATE SYSTEM]{ui.RESET}")
                
                choice = input(f"\n{ui.BOLD}Selection ❯ {ui.RESET}")

                if choice == '1':
                    # Reset the engine with a fresh state for a new mission
                    engine = LangChainEngine(selected_model, ui, tool_manager)
                    continue
                elif choice == '2':
                    continue 
                elif choice == '3':
                    selected_model = ui.select_model()
                    engine = LangChainEngine(selected_model, ui, tool_manager)
                elif choice == '0':
                    break
            else:
                print("No goal provided.")

    except KeyboardInterrupt:
        print("\n\n[SYSTEM]: INTERRUPT DETECTED. SHUTTING DOWN...")
    except Exception as e:
        ui.log_error(f"System Crash: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n{ui.DIM}[SYSTEM]: SESSION CLOSED.{ui.RESET}")