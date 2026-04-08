# ---------------------------------------------------
# IMPORTS
# ---------------------------------------------------

import os  
# 👉 Allows interaction with the operating system
# Used here to read environment variables (like API keys)

import json  
# 👉 Used to convert Python objects ↔ JSON format
# Example:
# dict → string (json.dumps)
# string → dict (json.loads)

from dotenv import load_dotenv  
# 👉 Loads variables from a .env file into your program
# This is where you store secrets like API keys safely

from app.services import tools as tool_functions  
# 👉 Imports your custom tool functions
# Example:
# tool_functions.open_google()
# tool_functions.add_event()

from openai import OpenAI  
# 👉 Official OpenAI client to communicate with GPT models

# ---------------------------------------------------
# LOAD ENV VARIABLES
# ---------------------------------------------------

load_dotenv()
# 👉 Reads the .env file and makes variables accessible via os.getenv()
#
# Example:
# .env file contains:
# OPENAI_API_KEY=sk-xxxxx
#
# Now you can access it with:
# os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------
# INITIALIZE OPENAI CLIENT
# ---------------------------------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# 👉 Creates a client object to talk to OpenAI API
#
# api_key is required to authenticate your requests


# ---------------------------------------------------
# SIMPLE CHAT FUNCTION (NO TOOLS)
# ---------------------------------------------------

def get_ai_response(user_text):
    """
    Basic chat response without tools.
    (Currently disabled to avoid API usage)
    """

    # ❌ Disabled version (costs money)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_text}
        ]
    )

    return response.choices[0].message.content
    

    


# ---------------------------------------------------
# TOOL DEFINITIONS (WHAT THE AI IS ALLOWED TO USE)
# ---------------------------------------------------

tools = [
    # ---------------- OPEN GOOGLE ----------------
    {
        "type": "function",
        "function": {
            "name": "open_google",
            "description": "Open Google in browser",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

    # ---------------- SEARCH GOOGLE ----------------
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Search something on Google",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}  # what to search
                },
                "required": ["query"]
            }
        }
    },

    # ---------------- ADD CALENDAR EVENT ----------------
    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Add an event to calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "time": {"type": "string"}  # ideally ISO format
                },
                "required": ["title", "time"]
            }
        }
    },

    # ---------------- GET CALENDAR EVENTS ----------------
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Get all calendar events",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# 👉 This list is sent to OpenAI
# It tells the AI:
# "You can use these functions if needed"


# ---------------------------------------------------
# TOOL EXECUTION ROUTER
# ---------------------------------------------------

def handle_tool_call(tool_call):
    """
    Executes the tool requested by the AI.

    The AI DOES NOT execute Python itself.
    It only says: "Call this function with these arguments".
    This function actually runs it.
    """

    name = tool_call.function.name  
    # 👉 Name of the tool (e.g., "search_google")

    args = json.loads(tool_call.function.arguments or "{}")
    # 👉 Convert JSON string → Python dict
    # Example:
    # '{"query": "Python"}' → {"query": "Python"}

    # Match tool name and execute corresponding function

    if name == "open_google":
        return tool_functions.open_google()

    elif name == "search_google":
        return tool_functions.search_google(**args)

    elif name == "add_event":
        return tool_functions.add_event(**args)

    elif name == "get_events":
        return tool_functions.get_events()

    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------
# MAIN AGENT FUNCTION (BRAIN OF YOUR SYSTEM)
# ---------------------------------------------------

def run_agent(messages, max_steps=5):
    """
    Multi-step AI agent loop.

    messages → full conversation history
    max_steps → safety limit to avoid infinite loops

    Flow:
    1. Send messages to AI
    2. AI may request tool
    3. Execute tool
    4. Send result back to AI
    5. Repeat until AI gives final answer
    """

    for step in range(max_steps):
        print(f"\n--- Step {step + 1} ---")

        # ---------------------------------------------------
        # CALL OPENAI (AI THINKING STEP)
        # ---------------------------------------------------

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        msg = response.choices[0].message
        # 👉 AI response (can be text OR tool call)

        # Save AI message into conversation history
        messages.append(msg)

        # ---------------------------------------------------
        # IF AI DECIDES TO USE A TOOL
        # ---------------------------------------------------

        if msg.tool_calls:
            # 👉 AI is asking to use a function

            for tool_call in msg.tool_calls:
                print(f"Using tool: {tool_call.function.name}")

                # Execute tool in Python
                result = handle_tool_call(tool_call)

                # Send tool result back to AI
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            # Continue loop → AI will see tool result next
            continue

        # ---------------------------------------------------
        # IF NO TOOL → FINAL ANSWER
        # ---------------------------------------------------

        print("Final answer reached.")
        return msg.content

    # ---------------------------------------------------
    # SAFETY STOP (avoid infinite loops)
    # ---------------------------------------------------

    return "Stopped after max steps (possible loop)."