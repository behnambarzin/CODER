===============================================================================
                                  CODER
                    Semi Autonomous Coding & Intelligence 
===============================================================================

DESCRIPTION
-----------
CODER is a high-fidelity autonomous agent designed to bridge the gap between 
large language models and local system execution. Unlike standard AI 
chatbots, CODER does not just "suggest" code; it plans, executes, verifies, 
and debugs code within your local environment.

By utilizing a state-based architecture, CODER can navigate complex file 
structures, perform deep code analysis, and manage system processes with 
minimal human intervention.

THE ENGINE: LANGCHAIN & THE NODE SYSTEM
----------------------------------------
CODER is built upon the LangChain ecosystem, specifically utilizing 
LangGraph to create a "Cognitive Workflow."

1. What is LangChain?
   LangChain is a framework that allows AI models to interact with the real 
   world. It provides the "connectors" (Tools) that allow the LLM to read 
   files, run terminal commands, and perform mathematical calculations.

2. The Node System (State-Graph Architecture):
   Instead of a simple back-and-forth conversation, CODER operates using a 
   system of "Nodes." Think of Nodes as specialized stations in a factory:
   
   • THE LLM NODE (Cognition): The brain analyzes the current situation and 
     decides what to do next.
   • THE ACTION NODE (Kinetic): The hands of the agent. This node executes 
     the tools (writing files, running scripts).
   • THE HUMAN NODE (Intervention): A safety checkpoint where the agent 
     pauses to ask for your strategic guidance if it hits a wall.
   • THE ERROR NODE (Recovery): If a command fails, this node analyzes 
     the error and instructs the brain on how to pivot.
   • THE COMPLETE NODE (Synthesis): The final station that compiles all 
     results into a polished technical summary.

This "Graph" ensures that the agent remains purposeful, follows a logical 
roadmap, and can recover from mistakes without crashing.

CORE FEATURES
-------------
• Autonomous Problem Solving: Turns high-level goals into actionable tasks.
• Structural Code Intelligence: Uses AST (Abstract Syntax Tree) to map out 
  how your Python functions and classes are connected.
• Precision File Management: Surgical ability to read, write, append, or 
  replace specific lines of code without corrupting files.
• Sandboxed Execution: Runs generated code in a controlled environment to 
  verify accuracy before concluding the mission.
• Local-First Privacy: Powered by Ollama, meaning your code and data never 
  leave your local machine.


INSTALLATION
------------
1. Python (Version 3.10 or higher)

2. Ollama (Local LLM Engine)
   - Download from: https://ollama.com/
   - Ensure the service is running in your system tray.

3. Install the required libraries:
   pip install langchain_ollama langgraph pydantic typing_extensions psutil


RUNNING IN VS CODE (STEP-BY-STEP)
---------------------------------
To ensure CODER has access to all its tools, follow these steps in VS Code:

1. OPEN FOLDER: 
   Open VS Code > File > Open Folder... > Select your project folder.

2. OPEN THE INTEGRATED TERMINAL:
   - Go to Terminal > New Terminal (at the top of the screen).

3. START THE AGENT:
   - Type the following and press Enter:
     python CODER.py

===============================================================================
                          END OF DOCUMENT
===============================================================================
