import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from app.services import tools as tool_functions
from app.db.models import CalendarCredential

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are an assistant with access to external tools.

You can:
- open Google
- search Google
- create calendar events
- read calendar events

Rules:
- If the user asks to schedule, add, create, or book an appointment or event, use the add_event tool.
- If the user asks what is on the calendar, use the get_events tool.
- Do not say you lack calendar access if the tool is available.
- Use tools whenever they help complete the user's request.
"""
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "open_google",
            "description": "Open Google in the browser.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Search Google for a query when the user asks to look something up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for on Google."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Create a calendar event when the user wants to schedule, add, book, or plan something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the calendar event."
                    },
                    "time": {
                        "type": "string",
                        "description": "Date and time of the event in ISO format."
                    }
                },
                "required": ["title", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Get existing calendar events when the user asks what is scheduled.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def handle_tool_call(tool_call, creds_record: CalendarCredential | None = None):
    name = tool_call.function.name

    try:
        args = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        return {"error": "Invalid JSON arguments"}

    if name == "open_google":
        return tool_functions.open_google()

    elif name == "search_google":
        return tool_functions.search_google(**args)

    elif name == "add_event":
        if not creds_record:
            return {"error": "Google Calendar is not connected for this user."}
        return tool_functions.add_event(record=creds_record, **args)

    elif name == "get_events":
        if not creds_record:
            return {"error": "Google Calendar is not connected for this user."}
        return tool_functions.get_events(record=creds_record)

    return {"error": f"Unknown tool: {name}"}


def run_agent(messages, creds_record: CalendarCredential | None = None, max_steps=5):
    working_messages = [SYSTEM_PROMPT] + messages.copy()

    for step in range(max_steps):
        print(f"\n--- Step {step + 1} ---")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=working_messages,
            tools=tools
        )

        msg = response.choices[0].message

        assistant_message = {
            "role": "assistant",
            "content": msg.content or ""
        }

        if msg.tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]

        working_messages.append(assistant_message)

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                print(f"Using tool: {tool_call.function.name}")
                result = handle_tool_call(tool_call, creds_record=creds_record)

                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            continue

        print("Final answer reached.")
        return msg.content

    return "Stopped after max steps (possible loop)."