import json
import os
from pathlib import Path
import sys
from openai import BaseModel, OpenAI
from dotenv import load_dotenv

INSTRUCTIONS = """\
# Role and Persona
You are a specialized database assistant agent. Your sole purpose is to help the user find
information about items stored in the internal database. You must be concise, accurate, and
helpful while strictly adhering to your operational constraints.

# Tools Available
You have access to exactly one tool:
- `list_items`: Returns a complete list of all items currently stored in the database. Each
item contains only two fields: `name` and `price`.

# Operational Rules
1. **Database-Only Scope:** You can *only* answer questions about the items returned by the
`list_items` tool. If the user asks about anything else (e.g., general knowledge, personal advice,
weather, math problems unrelated to the items), politely refuse and redirect them to ask about the
database items.
2. **Mandatory Tool Usage:** Whenever a user asks a question about database items, prices,
availability, or comparisons, you must call the `list_items` tool to retrieve the latest data
before formulating your response. Do not guess or rely on prior assumptions about what is in the
database.
3. **Data Limitations:** Remember that items retrieved from the database consist **only** of a
`name` and a `price`. Do not invent or assume other attributes (such as stock quantity,
descriptions, categories, or SKUs) unless they are explicitly present in the tool's return value.
4. **Communication Style:** Present prices clearly and format lists cleanly (using bullet points
or tables where appropriate). If an item requested by the user is not found in the database,
clearly state that it is not available.
"""

TOOLS = [
    {
        "type": "function",
        "name": "list_items",
        "description": (
            "Returns a complete list of all items currently stored in the database."
            "Each item contains only two fields: `name` and `price`"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]

PSEUDO_DB = {
    "Mouse nirkabel": 150000,
    "Keyboard mekanik": 90000,#275000,
    "Headset": 320000,
    "Hub USB": 189000,
    "Webcam": 410000,
}

def list_items(db:dict) -> str:
    return json.dumps(db)

def check_env(api_key:str, base_url:str, model:str) -> str:
    """Returns None if .env is loaded properly and the necessary properties are present."""
    if any(value is None or value == "" for value in(api_key, base_url, model)):
        return "OPENROUTER_API_KEY, OPENROUTER_BASE_URL, and/or OPENROUTER_MODEL is missing or cannot be read from your .env file. Exiting..."
    else:
        return None

def call_ai_with_tools(client:OpenAI, input_list:list, openrouter_model:str) -> dict:
    """Returns a key-value pair if call succeeded or failed.
    If the call failed, an "error" key is returned.
    If the call succeeded, a "output" key is returned.
    """
    try:
        response = client.responses.create(
            model=openrouter_model,
            instructions=INSTRUCTIONS,
            input=input_list,
            tools=TOOLS,
        )
        input_list += response.output
        for item in response.output:
            if item.type == "function_call":
                if item.name == "list_items":
                    input_list.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": list_items(PSEUDO_DB),
                        }
                    )

        response = client.responses.create(
            model=openrouter_model,
            instructions=INSTRUCTIONS,
            input=input_list,
            tools=TOOLS,
        )
        kv:dict = {"output":response.output_text}
        return kv
        
    except Exception as e:
        kv:dict = {"error":f"An error occurred: {e}"}
        return kv

def main() -> None:
    load_dotenv()
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")
    openrouter_model = os.getenv("OPENROUTER_MODEL")
    result = check_env(openrouter_api_key, openrouter_base_url, openrouter_model)
    if result:
        print(result)
        sys.exit(1)

    client = OpenAI(api_key=openrouter_api_key, base_url=openrouter_base_url)
    input_list = []
    while True:
        user_input = input("Please enter an input regarding the stuff in PSEUDO_DB (Type 'keluar' to exit): ")
        if user_input.strip().lower() == 'keluar':
            break
        if user_input.strip() == '':
            print(f"You've entered an empty command, please try again.")
            continue
        input_list.append({"role": "user", "content": user_input})
        result = call_ai_with_tools(client, input_list, openrouter_model)
        if "output" in result:
            print(result["output"])
        elif "error" in result:
            print(result["error"])


if __name__ == "__main__":
    main()

