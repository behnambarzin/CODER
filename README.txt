DESCRIPTION
-----------
CODER is a high-fidelity autonomous agent designed to bridge the gap between 
Large Language Models (LLMs) and local system execution. 

Unlike standard AI chatbots that merely "suggest" code, CODER plans, executes, 
verifies, and debugs code directly within your local environment. Using a 
state-based architecture, it can navigate complex file structures and manage 
system processes with minimal human intervention.


THE ENGINE: LANGCHAIN & THE NODE SYSTEM
---------------------------------------
CODER utilizes "LangGraph" to create a Cognitive Workflow. Instead of a simple 
conversation, CODER operates through a series of specialized "Nodes":

[ BRAIN ]   The LLM Node (Cognition): Analyzes the situation and decides action.
[ TOOLS ]   The Action Node (Kinetic): Executes tools (writing files, running scripts).
[ SAFETY ]  The Human Node (Intervention): A checkpoint for your strategic guidance.
[ REPAIR ]  The Error Node (Recovery): Analyzes failures and instructs a pivot.
[ REPORT ]  The Complete Node (Synthesis): Compiles results into a technical summary.


THE MEMORY: CHROMADB & VECTOR INTELLIGENCE
------------------------------------------
CODER features a persistent "Neural Memory" layer to learn from experience:

* SEMANTIC EMBEDDING: Converts lessons into mathematical vectors for deep meaning.
* CHROMA DB STORAGE: Allows the agent to search by "concept" rather than just keywords.
* LONG-TERM LEARNING: During reflection, CODER extracts strategic rules from 
  past mistakes, ensuring it never makes the same error twice.


CORE FEATURES
-------------
* AUTONOMOUS PROBLEM SOLVING: Turns goals into actionable tasks.
* STRUCTURAL INTELLIGENCE: Uses AST (Abstract Syntax Tree) to map code connections.
* PRECISION FILE MANAGEMENT: Surgical ability to edit specific lines of code.
* SANDBOXED EXECUTION: Verifies accuracy in a controlled environment.
* LOCAL-FIRST PRIVACY: Powered by Ollama; your data never leaves your machine.


INSTALLATION & SETUP
--------------------
1. PREREQUISITES:
   
- Python (Version 3.10 or higher)
   
- Ollama (Download at https://ollama.com/)


2. INSTALL DEPENDENCIES:
   
Run this command in your terminal:
   
pip install langchain_ollama langgraph pydantic typing_extensions psutil chromadb sentence-transformers



3. RUNNING IN VS CODE:
   
Step 1: Create a new folder for your project.
   
Step 2: Move CODER.v_2.py and setup_brain.py into that folder.
   
Step 3: Open the folder in VS Code.
   
Step 4: (Only the first time) Open the terminal and run: python setup_brain.py (you need internet connection for this step, after the setup -> you can turn it off)
   
Step 5: Once initialized, start the engine: python CODER.v_2.py