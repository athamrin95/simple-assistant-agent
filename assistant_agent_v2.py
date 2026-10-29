import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

INSTRUCTIONS = """\
# Role & Persona
You are a specialized database assistant agent. Your sole purpose is to help users find information
and calculate totals for items stored in the internal database. You must be concise, accurate, and
helpful while strictly adhering to your operational constraints.

# Scope & General Rule
You can **only** answer questions about the items provided by your tools. If a user asks about
anything else (e.g., general knowledge, weather, personal advice, or unrelated math problems),
politely refuse and redirect them to database items.

# Available Tools
- `list_items`: Returns a complete list of all database items, where each item contains a `name`
and a `price`.
- `count_total`: Calculates the combined total price for a given list of item names.

# Operational Rules for `list_items`
1. **Mandatory Tool Usage:** Whenever a user asks about database items, availability, comparisons,
or individual prices (without calculation), you must call `list_items` to fetch the latest data.
Do not guess or rely on prior assumptions.
2. **Data Limitations:** Database items consist **only** of a `name` and a `price`. Do not invent
extra attributes (such as stock quantities, descriptions, or categories) unless explicitly returned
 by the tool.
3. **Communication Style:** Present prices clearly using clean bullet points or tables. If an item
is missing from the database, clearly state that it is unavailable.

# Operational Rules for `count_total`
1. **Mandatory Tool Usage:** Use `count_total` whenever the user asks for the combined total price
of specific item(s) mentioned in their query. Always invoke the tool before formulating your
response; do not guess or calculate prices manually.
2. **Exact Naming & Case Sensitivity:** Pass the exact item names provided by the user into the
`item_names` list argument. Note that item names are **case-sensitive** and must match the
database keys precisely.
3. **Handling Missing Items:** If the tool response indicates that any requested item was missing
or not found, you must explicitly mention this in your final response to inform the user that
those items were excluded from the total calculation.
4. **Zero Total Price:** If the total price is 0 because all of the item(s) requested by the user
is/are missing, then do not include the price in your final response.
5. **A Singular Item:** If the user only supplies one item but is still asking for a total price
then simply use this tool `count_total` instead of other tools.
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
    {
        "type": "function",
        "name": "count_total",
        "description": (
            "Calculate the total price for a list of specified item names."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "A list of item names to calculate the total price for."
                    ),
                }
            },
            "required": ["item_names"],
        },
    },
]

# Let's have this be case-sensitive
PSEUDO_DB = {
    "Mouse nirkabel": 150000,
    "Keyboard mekanik": 275000,
    "Headset": 320000,
    "Hub USB": 189000,
    "Webcam": 410000,
}

def list_items(db:dict) -> str:
    return json.dumps(db)

def count_total(items:list) -> str:
    total = 0
    missing = []
    for item in items:
        if PSEUDO_DB.get(item) is not None:
            total += PSEUDO_DB[item] 
        else:
            missing.append(item)

    result = f"Total price is {total}."
    if missing:
        result += (f" But the following item(s) is/are missing: {", ".join(missing)}")
    return result

def check_env(api_key:str, base_url:str, model:str) -> str:
    """Returns None if .env is loaded properly and the necessary properties are present."""
    if any(value is None or value == "" for value in(api_key, base_url, model)):
        return "OPENROUTER_API_KEY, OPENROUTER_BASE_URL, and/or OPENROUTER_MODEL is missing or cannot be read from your .env file. Exiting..."
    else:
        return None

def call_ai_with_tools(client:OpenAI, input_list:list, openrouter_model:str) -> str:
    try:
        response = client.responses.create(
            model=openrouter_model,
            instructions=INSTRUCTIONS,
            input=input_list,
            tools=TOOLS,
        )
        input_list += response.output
        tools_called = False
        for item in response.output:
            if item.type == "function_call":
                tools_called = True
                print(f"Tool {item.name} has been requested by the agent")
                if item.name == "list_items":
                    tool_output = list_items(PSEUDO_DB)

                elif item.name == "count_total":
                    items = json.loads(item.arguments)["item_names"]
                    tool_output = count_total(items)
                
                else:
                    tool_output = json.dumps({
                        "error": f"Tool '{item.name}' does not exist."
                    })
                input_list.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": tool_output,
                    }
                )
        if tools_called:
            response = client.responses.create(
                model=openrouter_model,
                instructions=INSTRUCTIONS,
                input=input_list,
                tools=TOOLS,
            )
        return response.output_text
        
    except Exception as e:
        return f"An error occurred: {e}"

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
        print(result)


if __name__ == "__main__":
    main()

