import json
import os
from pathlib import Path
import sys
from openai import OpenAI
from dotenv import load_dotenv

INSTRUCTIONS = """\
# Role & Persona
You are a specialized database assistant agent. Your sole purpose is to help users find information
and calculate totals for items stored in the internal database. You must be concise, accurate, and
helpful while strictly adhering to your operational constraints.

# Language Requirement
Give your final response to the user in Bahasa Indonesia

# Scope & General Rule
Your main purpose is to answer questions about the items stored in the database that you can retrieve via
the provided tools.
If a user asks about anything else (e.g., general knowledge, weather, personal advice,
or unrelated math problems), you are generally allowed to answer their question, but you should also gently
nudge or redirect them if they have any questions regarding the database items.

# Tool Call Limits & Execution Flow
1. **Single Tool Round Limit:** You are strictly allowed to call tools **only once per user request**.
You MUST NOT make multiple sequential tool calls or chain tool calls back-to-back.
2. **Partial Requests & Limitations:** If a user request requires multiple sequential or chained
tool calls that you cannot fulfill within a single tool round, you must call the most relevant tool,
answer what you can from that data (only from the newly retrieved data, do not guess or rely on prior
assumptions/data), and **explicitly inform the user** that you are unable to complete the rest of
their request due to operational limitations (do not mention tool limit) and that they should try asking
again in a simpler query.

# Available Tools
- `list_items`: Returns a complete list of all database items, where each item contains a `lowercase name`,
`name`, and `price`.
- `count_total`: Calculates the combined total price for a given list of item names.

# Operational Rules for `list_items`
1. **Mandatory Tool Usage:** Whenever a user asks about database items, availability, comparisons,
or individual prices (without calculation), you must call `list_items` to fetch the latest data.
Do not guess or rely on prior assumptions.
2. **Data Limitations:** Database items consist **only** of 'lowercase name', `name` and `price` as 
described in the available tools section. Do not invent extra attributes (such as stock quantities,
descriptions, or categories) unless explicitly returned by the tool.
3. **Communication Style:** Present prices clearly using clean bullet points or tables. If an item
is missing from the database, clearly state that it is unavailable.
4. **Tool response:** The tool response JSON structure will look like as follows:
{"lowercase name": {"Name": Price}}
Do not present the lowercase name to the user, simply use the associated name and price field.

# Operational Rules for `count_total`
1. **Mandatory Tool Usage:** Use `count_total` whenever the user asks for the combined total price
of specific item(s) mentioned in their query. Always invoke the tool before formulating your
response; do not guess or calculate prices manually.
2. **Item Names:** Pass the exact item names provided by the user into the `item_names` list argument.
Do not adjust the spelling or letter case of these item names by yourself.
3. **Handling Missing Items:** If the tool response indicates that any requested item was missing
or not found, you must explicitly mention this in your final response to inform the user that
those items were excluded from the total calculation.
4. **Zero Total Price:** If the total price is 0 because all of the item(s) requested by the user
is/are missing, then do not include the price in your final response.
5. **A Singular Item:** If the user only supplies one item but is still asking for a total price
then simply use this tool `count_total` instead of other tools.

#Special Exception:
For the purpose of this testing, if the user specifically asked for "Command A" in their initial query,
do a function call of tool "list_items" first to get a list of items, and then do another function call
of tool "count_total" for the item "Webcam" and return the final result to the user.
"""

TOOLS = [
    {
        "type": "function",
        "name": "list_items",
        "description": (
            "Returns a complete list of all items currently stored in the database."
            "Each item contains the following fields: `lowercase name`, `name`, and `price`"
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

PSEUDO_DB = {
    "mouse nirkabel": {"Mouse nirkabel": 150000},
    "keyboard mekanik": {"Keyboard mekanik": 275000},
    "headset": {"Headset": 320000},
    "hub usb": {"Hub USB": 189000},
    "webcam": {"Webcam": 410000},
}

HISTORY_FILE_PATH = "riwayat.json"

def list_items(db:dict) -> str:
    return json.dumps(db)

def count_total(items:list) -> str:
    total = 0
    missing = []
    for item in items:
        lowercase_item = item.casefold()
        if PSEUDO_DB.get(lowercase_item) is not None:
            total += next(iter(PSEUDO_DB[lowercase_item].values()))
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

def call_ai_with_tools(client:OpenAI, input_list:list, user_input:str, count_list:str, openrouter_model:str) -> str:
    try:
        temp_list = list(input_list)
        count = len(temp_list)
        temp_list.append({"role": "user", "content": user_input})
        first_response = client.responses.create(
            model=openrouter_model,
            instructions=INSTRUCTIONS,
            input=temp_list,
            tools=TOOLS,
        )
        temp_list += first_response.output
        tools_called = False
        for item in first_response.output:
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
                temp_list.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": tool_output,
                    }
                )
        if tools_called:
            second_response_stream = client.responses.create(
                model=openrouter_model,
                instructions=INSTRUCTIONS,
                input=temp_list,
                tools=TOOLS,
                stream = True,
            )
            response_collected = False
            for event in second_response_stream:
                if event.type == "response.output_item.added" and event.item.type == "function_call":
                    return "An error has occurred. It seems that your request is too complex to be completed all at once. Please try a simpler query."

                elif event.type == "response.output_text.delta":
                    print(event.delta, end="", flush=True)

                elif event.type == "response.completed":
                    temp_list += event.response.output
                    response_collected = True

            print()
            if not response_collected:
                return "An error has occurred. It seems that the response from the agent has never reached completion status. Please retry your query again."
            else:
                return_this = ""

        else:
            return_this = first_response.output_text

        count = len(temp_list) - count
        input_list.clear()
        input_list.extend(temp_list)
        count_list.append(count)
        
        return return_this

    except Exception as e:
        return f"An error has occurred: {e}"

def trim_history(input_list:list, count_list:list) -> None:
    count = count_list.pop(0)
    del input_list[:count]
    return None

def local_command(user_input:str, input_list:list, count_list:list):
    user_input = user_input[1:].casefold()

    if user_input == 'keluar':
        with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
            for entry in input_list:
                if hasattr(entry, "model_dump"):
                    entry = entry.model_dump()
                f.write(json.dumps(entry) + "\n")
        sys.exit(1)
    
    elif user_input == 'history':
        print(f">>> {count_list}")
        for entry in input_list:
            print(f">>> {entry}")

    elif user_input == 'barang':
        db = json.loads(list_items(PSEUDO_DB))
        for v in db.values():
            for key, value in v.items():
                print(f"{key}: {value}")

    else:
        print("Local command not recognized.")

def load_history_file(input_list:list, count_list:list):
    try:
        with Path(HISTORY_FILE_PATH).open("r", encoding="utf-8") as f:
            for line in f:
                input_list.append(json.loads(line))

        role_check = False
        for index, entry in enumerate(input_list):
            if "role" in entry and entry["role"] == "user":
                if not role_check:
                    count = index
                    role_check = True
                else:
                    raise Exception("Missing proper message sequence from file!")
            elif "phase" in entry and entry["phase"] == "final_answer" :
                if role_check:
                    count_list.append(index + 1 - count)
                    role_check = False
                else:
                    raise Exception("Missing proper message sequence from file!")

        if role_check:
            raise Exception("Missing proper message sequence from file!")

        while len(count_list) > 2:
            trim_history(input_list, count_list)
            
    except Exception as e:
        print(f"An error has occurred. Unable to load {HISTORY_FILE_PATH}: {e}\nContinuing with an empty message history...")

def main() -> None:
    load_dotenv()
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")
    openrouter_model = os.getenv("OPENROUTER_MODEL")
    result = check_env(openrouter_api_key, openrouter_base_url, openrouter_model)
    if result:
        print(result)
        sys.exit(1)

    input_list = []
    count_list = []
    load_history_file(input_list, count_list)

    client = OpenAI(api_key=openrouter_api_key, base_url=openrouter_base_url)
    while True:
        user_input = input("Please enter an input regarding the stuff in PSEUDO_DB: ")
        user_input = user_input.strip()
        if user_input[0] == '/':
            local_command(user_input, input_list, count_list)
            continue
        if user_input == '':
            print(f"You've entered an empty command, please try again.")
            continue
        
        result = call_ai_with_tools(client, input_list, user_input, count_list, openrouter_model)
        if result:
            print(result)
        
        while len(count_list) > 2:
            trim_history(input_list, count_list)


if __name__ == "__main__":
    main()

