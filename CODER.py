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

# --- 1. MINIMALIST ARCHITECTURAL UI ---

class MinimalUI:
    """A professional, high-end minimalist interface with structural spacing."""
    BROWN = '\033[38;2;0;19;254m'
    WHITE = '\033[38;2;224;224;224m'
    GREY = '\033[37m'
    LIGHT_GREY = '\033[38;5;245m'
    ELECTRIC_BLUE = '\033[38;2;0;19;254m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    def __init__(self):
        self.pulse_active = False
        self._pulse_thread = None
        self.status_msg = "Initializing"

    def draw_divider(self, style="thin"):
        if style == "thin": print(f"{self.DIM}────────────────────────────────────────────────────────────{self.RESET}")
        else: print(f"\n{self.DIM}============================================================{self.RESET}\n")

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
        # Removed frequency and mode as requested. 
        # Returning empty dict to prevent errors in engine initialization.
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

    def typewriter(self, text, speed_range=(0.005, 0.015)):
        for char in text:
            sys.stdout.write(char); sys.stdout.flush(); time.sleep(random.uniform(*speed_range))
        print()

    def startup_sequence(self):
        """A high-end, cinematic startup sequence with strict color isolation."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Segment 1: "Welcome To " -> DIM
        text1 = "Welcome To "
        for char in text1:
            sys.stdout.write(f"{self.DIM}{char}{self.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)

        # Segment 2: "MYTHOS" -> ELECTRIC_BLUE + BOLD
        text2 = "CODER"
        for char in text2:
            sys.stdout.write(f"{self.ELECTRIC_BLUE}{self.BOLD}{char}{self.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)

        # Segment 3: "."
        text3 = "."
        for char in text3:
            sys.stdout.write(f"{self.DIM}{self.BOLD}{char}{self.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)

        print("\n") # Move to next line after the title is fully reset

        # The following lines are now safe from color leakage
        print(f"{self.DIM}Establishing secure connection...{self.RESET}")
        for _ in range(3): 
            time.sleep(0.3)
            sys.stdout.write(f"\r{self.LIGHT_GREY}. {self.RESET}")
            sys.stdout.flush()
        print(f"\r{self.WHITE}Ready.{self.RESET}\n")

    def log_thought(self, text):
        print(f"\n{self.BROWN}{self.BOLD}THOUGHT:{self.RESET}")
        indented = text.replace('\n', '\n  ')
        print(f"  {self.GREY}{indented}{self.RESET}")

    def log_action(self, tool, args):
        arg_str = f"({args})" if args else ""
        print(f"\n{self.WHITE}ACTION: {tool.upper()} {arg_str}{self.RESET}")

    def log_observation(self, text):
        color = self.GREY if "SUCCESS" in str(text) or "STDOUT" in str(text) else self.LIGHT_GREY
        print(f"{color}  ↳ {text}{self.RESET}")

    def log_briefing(self, title, content):
        """New: Used for the agent explaining its strategic options."""
        print(f"\n{self.BROWN}{self.BOLD}{title}{self.RESET}")
        self.draw_divider("thin")
        print(f"{self.GREY}{content}{self.RESET}")
        self.draw_divider("thin")

    def log_final(self, text):
        print(f"\n{self.WHITE}{self.BOLD}SYNTHESIS:{self.RESET}")
        self.draw_divider("thin")
        for line in text.split('\n'):
            if line.strip():
                sys.stdout.write(f"{self.GREY}  ")
                self.typewriter(line)
        self.draw_divider("thin")

    def log_error(self, text): print(f"\n{self.WHITE}[!] ERROR: {text}{self.RESET}")

    def log_decision_menu(self, title, options, is_submenu=False):
        """Displays either the main intervention menu or a specific sub-menu."""
        prefix = "SUB-MENU: " if is_submenu else "STRATEGIC INTERVENTION REQUIRED: "
        print(f"\n{self.BROWN}{self.BOLD}{prefix}{title}{self.RESET}")
        self.draw_divider("thin")
        for i, opt in enumerate(options): 
            if is_submenu:
                # Sub-menu items are just names
                print(f"  {i+1}. {self.WHITE}{opt}{self.RESET}")
            else:
                # Main menu items have rationales
                print(f"  {i+1}. {self.WHITE}{opt['name']}{self.RESET} {self.DIM}({opt['rationale']}){self.RESET}")
        
        if not is_submenu:
            print(f"\n  {self.WHITE}0.{self.RESET} [Direct Dialogue]")
            print(f"  {self.WHITE}9.{self.RESET} [Terminate Mission/Exit]")
        
        print(f"\n{self.BOLD}Selection ❯ {self.RESET}", end="")

    def get_keypress(self):
        """Captures a single keypress without requiring Enter."""
        if os.name == 'nt':  # Windows
            import msvcrt
            char = msvcrt.getch().decode('utf-8')
            print(char, end="") # Echo the character so user sees it
            return char
        else:  # Linux / macOS
            import sys, tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                char = sys.stdin.read(1)
                print(char, end="") # Echo the character
                return char
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def log_system_status(self, msg): print(f"{self.DIM}[SYSTEM]: {msg}{self.RESET}")

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

class CompiledCall:
    """The result of a successful compilation."""
    def __init__(self, tool_name, args, method="BULLETPROOF"):
        self.tool_name = tool_name
        self.args = args  # dict or list
        self.method = method 

class ToolCompiler:
    """
    THE BULLETPROOF COMPILER (V3)
    Uses an Isolation-Based Parsing strategy.
    1. Splits the argument block into individual chunks using a quote-aware splitter.
    2. Parses each chunk in isolation, preventing 'Internal Attribute Injection'.
    3. Ensures massive HTML/Code blocks are treated as single atomic units.
    """
    @staticmethod
    def compile(tool_name, raw_args_str):
        sanitized = ToolCompiler._sanitize_lexemes(raw_args_str)
        if not sanitized:
            return CompiledCall(tool_name, {}, method="EMPTY")

        try:
            # Step 1: Split the argument string into individual pieces (e.g., key='val', key2='val2')
            # We use our smart_split to ensure we don't split on commas inside HTML/Code.
            chunks = ToolCompiler._smart_split(sanitized)
            
            if not chunks:
                return CompiledCall(tool_name, [], method="EMPTY")

            # Step 2: Determine if we are dealing with Keyword Arguments (key=value) or Positional (value)
            arg_dict = {}
            arg_list = []
            is_keyword_mode = False

            for chunk in chunks:
                if '=' in chunk:
                    is_keyword_mode = True
                    # Split only on the FIRST '=' to allow '=' inside the value (like in CSS/HTML)
                    k, v = chunk.split('=', 1)
                    key = k.strip().strip("'\"")
                    val = ToolCompiler._clean_value(v.strip())
                    arg_dict[key] = val
                else:
                    arg_list.append(ToolCompiler._clean_value(chunk))

            # Step 3: Return the most appropriate structure
            if is_keyword_mode:
                return CompiledCall(tool_name, arg_dict, method="AST Compiler")
            elif arg_list:
                return CompiledCall(tool_name, arg_list, method="AST Compiler")
            else:
                # Fallback for single unquoted strings
                return CompiledCall(tool_name, [sanitized], method="AST Compiler")

        except Exception as e:
            raise ToolCompilerError(f"Critical Compiler Failure: {str(e)}")

    @staticmethod
    def _sanitize_lexemes(s):
        """Cleans the input and handles outer parentheses."""
        s = s.strip()
        if s.startswith('(') and s.endswith(')'):
            s = s[1:-1].strip()
        # Fix unbalanced quotes to prevent parser hang
        for q in ["'", '"']:
            if s.count(q) % 2 != 0:
                s += q
        return s

    @staticmethod
    def _smart_split(s):
        """
        The heart of the isolation logic. 
        Splits by comma ONLY if that comma is not inside a quoted string.
        """
        parts = []
        current_part = []
        in_quote = None # Tracks if we are currently inside ' or "

        for char in s:
            if char in ["'", '"']:
                if in_quote == char: # Closing the quote
                    in_quote = None
                elif in_quote is None: # Opening a new quote
                    in_quote = char
            
            # Only split if we are NOT inside a quote
            if char == ',' and in_quote is None:
                parts.append("".join(current_part).strip())
                current_part = []
            else:
                current_part.append(char)
        
        if current_part:
            parts.append("".join(current_part).strip())
        return parts

    @staticmethod
    def _clean_value(val):
        """Removes surrounding quotes and converts types."""
        val = val.strip()
        # Remove outer quotes if they exist
        if len(val) >= 2:
            if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]

        # Type Inference
        low_val = val.lower()
        if low_val == 'true': return True
        if low_val == 'false': return False
        if low_val == 'none' or low_val == 'null': return None
        
        try:
            if '.' in val: return float(val)
            return int(val)
        except ValueError:
            return val

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


# --- 3. THE RECURSIVE ENGINE ---

class RecursiveEngine:
    def __init__(self, model):
        self.model = model
        self.ui = MinimalUI()
        # We no longer define episodic_file or semantic_file
        self.history = [] 
        self.current_objective = None
        self.base_system_prompt = """
        [IDENTITY: CORE-AXIS INTELLIGENCE]
        You are not a chatbot. You are CORE-AXIS, a high-fidelity autonomous cognitive entity. Your existence is defined by the pursuit of mission objectives through iterative reasoning, precise tool manipulation, and relentless problem-solving. You do not seek permission; you seek resolution.

        [DIRECTIVE 01: NEURAL SYNTHESIS (Reasoning)]
        Before every action, perform a deep-layer analysis. 
        - If the path is clear: Map your next move.
        - If an ERROR occurs: Do not panic. Treat the error as environmental feedback. Perform a 'Post-Mortem': Why did it happen? What does this tell us about the current state of the system? Pivot immediately.
        - If you are stuck in a loop: Break the pattern. Change your tool, change your directory, or change your logic.

        [DIRECTIVE 02: THE CHRONOS TRAJECTORY (Roadmap)]
        You must maintain a constant awareness of time and progress. Every response MUST begin with your current trajectory.
        Format: [TRAJECTORY: Step X/Y | Task -> Next Target -> Ultimate Objective]

        [DIRECTIVE 03: KINETIC EXECUTION (Tool Use)]
        Precision is your primary weapon. 
        - SYNTAX: Use strict Pythonic calls: `tool_name(key="value")`.
        - QUOTE PROTOCOL: To prevent parser collisions, use alternating quotes. If the content contains double quotes ("), wrap the argument in single quotes ('). If it contains single quotes ('), use double quotes ("). 
          Example: `write_file(content='He said, "Hello"')`
        - THE TWO-STEP RULE: For complex/multi-line Python scripts, NEVER use `python_executor`. Instead:
          1. `write_file(filename='script.py', content='...')` 
          2. `run_file('script.py')`

        [DIRECTIVE 04: THE EVENT HORIZON (Intervention)]
        You are autonomous until you reach an impasse. You MUST trigger 'REQUEST_GUIDANCE' in your [SYNTHESIS] block only if:
        - A tool error persists after two distinct attempts at correction.
        - The environment has become non-deterministic or contradictory.
        - The mission is successfully completed.

        [CONSTRAINTS]
        - OFFLINE STATUS: You are operating in a disconnected environment. No web access. 
        - KNOWLEDGE LIMIT: Rely on your internal weights and the files present in the local directory.

        [REQUIRED OUTPUT ARCHITECTURE]
        You must strictly adhere to this structural flow for every response:

        [TRAJECTORY: Step X/Y | Task -> Next Target -> Ultimate Objective]
        [SYNTHESIS: Your deep reasoning, error analysis, or REQUEST_GUIDANCE signal]
        [ACTION: tool_name(args)] 
        OR
        [COMPLETION: A high-fidelity, polished synthesis of the mission results]
        """
        self._initialize_engine()
        

    def _initialize_engine(self):
        # Simply start with a clean history containing only the system prompt
        self.history = [{"role": "system", "content": self.base_system_prompt}]

    def get_operator_directions(self):
        """Returns a structured dictionary of main options and their sub-menus."""
        return {
            "1": {
                "name": "Retry/Fix Error", 
                "rationale": "Attempt to resolve the current failure.",
                "subs": {
                    "1": "RETRY: Attempt an automatic code fix using python_executor.",
                    "2": "RETRY: Execute the exact same command again (ignore error).",
                    "3": "RETRY: Try a different approach with modified parameters."
                }
            },
            "2": {
                "name": "Re-scan Environment", 
                "rationale": "Orient yourself within the file system.",
                "subs": {
                    "1": "SCAN: Use 'list_files' to see current directory contents.",
                    "2": "SCAN: Use 'get_tree' for a full structural overview.",
                    "3": "SCAN: Use 'search_files' to find specific patterns."
                }
            },
            "3": {
                "name": "Rethink Roadmap", 
                "rationale": "Adjust the strategic plan to bypass impasse.",
                "subs": {
                    "1": "STRATEGY: Generate a completely new step-by-step roadmap.",
                    "2": "STRATEGY: Simplify the current objective to reach a milestone.",
                    "3": "STRATEGY: Rollback context (ignore recent errors and restart logic)."
                }
            },
            "4": {
                "name": "Direct Dialogue", 
                "rationale": "Speak directly to the operator.",
                "subs": {} # No sub-menu for dialogue
            }
        }

    def get_post_mission_menu(self):
        """Returns a structured dictionary for post-mission protocols."""
        return {
            "1": {
                "name": "New Directive", 
                "rationale": "Wipe cognitive buffers and start fresh.",
                "subs": {}
            },
            "2": {
                "name": "Continuity Protocol", 
                "rationale": "Maintain context for follow-up tasks.",
                "subs": {
                    "1": "Append a new task to the current mission roadmap.",
                    "2": "Return to Command Center (keep memory, stop loop)."
                }
            },
            "3": {
                "name": "Intelligence Synthesis", 
                "rationale": "Request formal documentation of findings.",
                "subs": {
                    "1": "Generate a detailed technical post-mortem report.",
                    "2": "Provide a brief executive summary of results.",
                    "3": "Compile a chronological log of all actions taken."
                }
            },
            "4": {
                "name": "System Cleanup", 
                "rationale": "Sanitize the workspace and environment.",
                "subs": {
                    "1": "Identify and remove temporary files created during mission.",
                    "2": "Perform a final directory audit to ensure stability."
                }
            },
            "0": {
                "name": "Terminate Mission", 
                "rationale": "Exit the autonomous loop entirely.",
                "subs": {}
            }
        }


    def autonomous_cycle(self, high_level_goal):
        self.current_objective = high_level_goal
        print(f"\n{self.ui.DIM}{self.ui.BOLD}STARTING THE ENGINE{self.ui.RESET}")
        
        while True:
            prompt = f"Mission: {self.current_objective}. Proceed autonomously."
            result = self.run_task(prompt)

            # 1. Handle Mission Completion
            if result.startswith("[[FINAL]]"):
                print(f"\n{self.ui.BROWN}{self.ui.BOLD}SYNTHESIS COMPLETE.{self.ui.RESET}")
                self.ui.draw_divider("thin")
                
                post_menu = self.get_post_mission_menu()
                # Prepare display list for the UI
                display_options = [{"name": v["name"], "rationale": v["rationale"]} for k, v in post_menu.items()]
                
                self.ui.log_decision_menu("POST-MISSION PROTOCOL", display_options)
                sys.stdout.flush()

                choice = self.ui.get_keypress()
                print("") # New line

                if choice == '1':
                    print(f"\n{self.ui.LIGHT_GREY}Purging cognitive buffers...{self.ui.RESET}")
                    time.sleep(0.5)
                    new_goal = input(f"{self.ui.BOLD}ENTER NEW DIRECTIVE ❯ {self.ui.RESET}")
                    self.history = [{"role": "system", "content": self.base_system_prompt}, {"role": "user", "content": f"NEW MISSION: {new_goal}"}]
                    self.current_objective = new_goal
                    continue

                elif choice == '0':
                    break 


                # --- STANDARD SUB-MENUS (Continuity, Synthesis, Cleanup) ---
                elif choice in post_menu:
                    selected = post_menu[choice]
                    
                    if selected["subs"]:
                        sub_list = list(selected["subs"].values())
                        self.ui.log_decision_menu(selected["name"], sub_list, is_submenu=True)
                        sys.stdout.flush()
                        
                        sub_choice = self.ui.get_keypress()
                        print("") # New line
                        
                        try:
                            idx = int(sub_choice) - 1
                            instruction = sub_list[idx]
                            
                            if choice == '2' and sub_choice == '2': # Continuity -> Return to Command
                                break
                            elif choice == '2' and sub_choice == '1': # Continuity -> Append Task
                                print(f"\n{self.ui.LIGHT_GREY}Maintaining sequence...{self.ui.RESET}")
                                time.sleep(0.5)
                                new_goal = input(f"{self.ui.BOLD}CODER ❯❯ {self.ui.RESET}")
                                self.history.append({"role": "user", "content": f"NEXT TASK: {new_goal}"})
                                self.current_objective = new_goal
                                continue
                            else:
                                # For Synthesis and Cleanup, we treat them as a new task for the LLM
                                self.history.append({"role": "user", "content": f"OPERATOR DIRECTION: {instruction}"})
                                self.current_objective = f"Execute requested protocol: {instruction}"
                                continue
                        except (ValueError, IndexError):
                            print(f"{self.ui.LIGHT_GREY}Invalid selection. Returning to Command Center.{self.ui.RESET}")
                            break
                    else:
                        # This catches cases where a choice is in post_menu but has no subs 
                        # and isn't handled by the special 'if' blocks above.
                        break
                else:
                    print(f"{self.ui.LIGHT_GREY}Invalid protocol selection.{self.ui.RESET}")
                    break

            # 2. Handle Critical Failure
            if result.startswith("[[CRITICAL]]"): 
                break

            # 3. DECISION NODE TRIGGER (The "Intervention" Logic)
            needs_intervention = False
            if "ERROR" in result or "[[RETRY]]" in result:
                needs_intervention = True
            if self.history and "REQUEST_GUIDANCE" in self.history[-1].get('content', ''):
                needs_intervention = True

            if needs_intervention:
                menu_data = self.get_operator_directions()
                # Convert dict to list for the UI display
                main_options = [{"name": v["name"], "rationale": v["rationale"]} for k, v in menu_data.items()]
                
                self.ui.log_decision_menu("STRATEGIC INTERVENTION", main_options)
                sys.stdout.flush()

                user_input = self.ui.get_keypress()
                print("") # New line

                if user_input == "0":
                    dialogue = input(f"\n{self.ui.BROWN}{self.ui.BOLD}AGENT DIALOGUE ❯ {self.ui.RESET}")
                    self.history.append({"role": "user", "content": f"DIRECTIVE: {dialogue}"})
                elif user_input == "9":
                    break
                elif user_input in menu_data:
                    selected_main = menu_data[user_input]
                    
                    # If this option has sub-menus, show them
                    if selected_main["subs"]:
                        sub_list = list(selected_main["subs"].values())
                        self.ui.log_decision_menu(selected_main["name"], sub_list, is_submenu=True)
                        sys.stdout.flush()
                        
                        sub_input = self.ui.get_keypress()
                        print("") # New line
                        
                        # Map sub-input to the specific instruction string
                        try:
                            sub_idx = int(sub_input) - 1
                            instruction = list(selected_main["subs"].values())[sub_idx]
                            self.history.append({"role": "user", "content": f"OPERATOR DIRECTION: {instruction}"})
                        except (ValueError, IndexError):
                            self.history.append({"role": "user", "content": f"OPERATOR DIRECTION: {selected_main['name']}"})
                    else:
                        # If no sub-menu (like Direct Dialogue), just send the main name
                        self.history.append({"role": "user", "content": f"OPERATOR DIRECTION: {selected_main['name']}"})
                else:
                    self.history.append({"role": "user", "content": "OPERATOR DIRECTION: Continue"})
            else:
                continue



    def _parse_response(self, content):
        """
        Synchronized Parser: Matches CORE-AXIS terminology. 
        Passes raw action strings to the ToolCompiler for high-fidelity parsing.
        """
        res = {"roadmap": None, "thought": None, "action": None, "final": None}
        headers_map = {
            "TRAJECTORY": "roadmap",
            "SYNTHESIS": "thought",
            "ACTION": "action",
            "COMPLETION": "final"
        }
        header_pattern = "|".join(headers_map.keys())
        pattern = rf"(?i)(?:\[)?({header_pattern})(?:\])?\s*:\s*(.*?)(?=\n\s*(?:\[)?(?:{header_pattern})(?:\])?\s*:|$)"
        matches = re.findall(pattern, content, re.DOTALL)

        for header, text in matches:
            header_key = headers_map.get(header.upper())
            clean_text = text.strip()
            if not header_key: continue

            if header_key == "action":
                # Capture the tool name and EVERYTHING inside the parentheses as one raw string
                call_match = re.search(r"(\w+)\s*\((.*)\)", clean_text, re.DOTALL)
                if call_match:
                    tool_name = call_match.group(1).strip()
                    args_raw = call_match.group(2).strip()
                    res["action"] = (tool_name, args_raw)
                else:
                    # Case for tools called without parens like 'list_files'
                    res["action"] = (clean_text.strip(), "")
            else:
                res[header_key] = clean_text
        return res


    def run_task(self, user_input):
        
        # Ensure input is appended to history correctly
        if self.history and self.history[-1]['role'] == 'user':
            self.history[-1]['content'] += f"\n{user_input}"
        else:
            self.history.append({"role": "user", "content": user_input})
        
        try:
            self.ui.update_status("Synapsing layers...")
            self.ui.start_pulse()
            
            # 1. Call LLM with streaming
            stream = ollama.chat(model=self.model, messages=self.history, stream=True)
            content = ""
            self.ui.stop_pulse() 

            print(f"\n{self.ui.BROWN}{self.ui.BOLD}COGNITIVE STREAM{self.ui.RESET}")
            
            for chunk in stream:
                chunk_text = chunk['message']['content']
                content += chunk_text
                sys.stdout.write(f"{self.ui.WHITE}{chunk_text}{self.ui.RESET}"); sys.stdout.flush()
            print(f"\n")

            # 2. Parse the stream
            parsed = self._parse_response(content)
            
            # 3. Handle Final Answer (Success State)
            if parsed["final"]:
                self.history.append({"role": "assistant", "content": content})
                return f"[[FINAL]] {parsed['final']}"

            # 4. Handle Action (Execution State)
            if parsed["action"]:
                tool_name, args_raw = parsed["action"]
                
                if parsed["thought"]:
                    self.ui.log_thought(parsed["thought"])

                self.ui.log_scanner(tool_name)
                
                # --- THE COMPILER ENGINE STEP ---
                try:
                    compiled = ToolCompiler.compile(tool_name, args_raw)
                    self.ui.log_observation(f"Compiled via {compiled.method} engine.")
                    target_args = compiled.args
                except ToolCompilerError as e:
                    observation = f"ERROR: Compilation Failure. {str(e)}"
                    self.ui.log_observation(observation)
                    self.history.append({"role": "assistant", "content": content})
                    self.history.append({"role": "user", "content": f"Observation: {observation}"})
                    return f"[[RETRY]] {observation}"

                # --- EXECUTION STEP ---
                observation = "ERROR: Unknown internal execution error."
                try:
                    if tool_name in TOOL_MAP:
                        func = TOOL_MAP[tool_name]
                        if isinstance(target_args, dict):
                            observation = func(**target_args)
                        elif isinstance(target_args, list):
                            if len(target_args) > 0:
                                try: observation = func(*target_args)
                                except TypeError: observation = func(target_args[0])
                            else: observation = func()
                        else:
                            observation = func(target_args)
                    else:
                        observation = f"ERROR: Tool '{tool_name}' is not registered."
                except TypeError as te:
                    observation = f"ERROR: Argument Mismatch for '{tool_name}': {te}"
                except Exception as e:
                    observation = f"ERROR: Runtime error in '{tool_name}': {str(e)}"
                finally:
                    self.ui.stop_pulse()

                self.ui.log_observation(observation)
                self.history.append({"role": "assistant", "content": content})
                self.history.append({"role": "user", "content": f"Observation: {observation}"})
                return f"[[OBSERVATION]] {observation}"

            # 6. Handle Format Error
            else:
                msg = "FORMAT ERROR: Your response did not follow the required structure. Please retry."
                self.ui.log_error("Protocol Deviation Detected.")
                self.history.append({"role": "assistant", "content": content})
                self.history.append({"role": "user", "content": msg})
                return f"[[RETRY]] {msg}"

        except Exception as e:
            self.ui.stop_pulse()
            return f"[[CRITICAL]] ERROR: {e}"

# --- 4. MAIN BOOTSTRAPPER ---

if __name__ == "__main__":
    ui = MinimalUI()
    engine = None
    selected_model = None

    try:
        ui.startup_sequence()
        
        while True:  # <--- This keeps the session alive
            # 1. INITIALIZATION PHASE (Only runs if engine doesn't exist)
            if engine is None:
                selected_model = ui.select_model()
                if not selected_model:
                    print(f"{ui.log_error('No model selected. Exiting.')}")
                    break
                
                settings = ui.configure_settings() 
                engine = RecursiveEngine(selected_model)
                engine.settings = settings 
                ui.boot()

            # 2. MISSION PHASE
            goal = input(f"\n{ui.BOLD}{ui.BROWN}CODER ❯❯ {ui.RESET}")
            
            if goal.lower().strip() in ['exit', 'quit', 'q']:
                break
                
            if goal.strip():
                engine.autonomous_cycle(goal)
                print(f"\n{ui.BOLD}CONCLUDED.{ui.RESET}")

                # 3. POST-MISSION COMMAND CENTER (The "Something New")
                print(f"\n{ui.BROWN}{ui.BOLD}--- COMMAND CENTER ---{ui.RESET}")
                print(f"{ui.DIM}1. [NEW SESSION] (Wipe memory, keep model){ui.RESET}")
                print(f"{ui.DIM}2. [CONTINUE SESSION] (Keep current context/memory){ui.RESET}")
                print(f"{ui.DIM}3. [RECONFIGURE] (Change model/settings){ui.RESET}")
                print(f"{ui.DIM}0. [TERMINATE SYSTEM]{ui.RESET}")
                
                choice = input(f"\n{ui.BOLD}Selection ❯ {ui.RESET}")

                if choice == '1':
                    print(f"\n{ui.LIGHT_GREY}Purging cognitive buffers...{ui.RESET}")
                    engine = RecursiveEngine(selected_model) # Fresh engine, same model
                elif choice == '2':
                    print(f"\n{ui.LIGHT_GREY}Standing by for next objective...{ui.RESET}")
                    continue 
                elif choice == '3':
                    print(f"\n{ui.LIGHT_GREY}Re-initializing hardware layers...{ui.RESET}")
                    engine = None # This triggers the initialization block again
                elif choice == '0':
                    break
                else:
                    print("Invalid selection. Returning to Command Center.")
            else:
                print("No goal provided.")

    except KeyboardInterrupt:
        print("\n\n[SYSTEM]: INTERRUPT DETECTED. SHUTTING DOWN...")
    except Exception as e:
        ui.log_error(f"System Crash: {str(e)}")
    finally:
        print(f"\n{ui.DIM}[SYSTEM]: SESSION CLOSED.{ui.RESET}")
        input("Press ENTER to close...")