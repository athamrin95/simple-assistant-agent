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
1. **Chained Tool Limit:** You are allowed to chain function calls consecutively up to a maximum of 4 times per user request.
However, if the number of function calls exceed the set maximum of times, you must **explicitly inform the user** that you are
unable to complete their request due to operational limitations and that they should try asking again in a simpler query.

# Available Tools
- `find_item`: Returns a complete list of all database items if no argument is given, or the details of an item
if an argument is given. This argument is the item's name.
- `count_total`: Calculates the combined total price for a given list of item names.

# Operational Rules for `find_item`
1. **Mandatory Tool Usage:** Whenever a user asks about database items, availability, comparisons,
or individual prices (without calculation), you must call `find_item` to fetch the latest data. Do not rely
on assumptions or prior knowledge.
2. **Data Limitations:** Database items consist **only** of `name` and `price`. Do not invent extra attributes
(such as stock quantities, descriptions, or categories) unless explicitly returned by the tool.
3. **Communication Style:** Present prices clearly using clean bullet points or tables. If an item
is missing from the database, clearly state that it is unavailable.
4. **Argument vs. No Argument:** This tool accepts no argument or an argument. If the user wishes to find all items
or gave no specific name, then simply provide no argument for the tool. If the user wishes to find some specified
item(s), then the item name from the user query must be passed down to the `item_name` string argument. Note that
if multiple names are provided, you must break them down to one `find_item` tool per item. For example, if the user
queries "I want to find the price of webcam and mouse", then you need to call for find_item("webcam") and
find_item("mouse").
5. **Partial or Fuzzy Name:** Assume that the user would always provide a partial, abbreviated,
or incomplete item name (e.g., asking for the price of "key" when the database contains "Keyboard mekanik").
As such, you must use the name provided from the response, assuming you get a positive response, as the official
name for your answer to the user's query.

# Operational Rules for `count_total`
1. **Never Used First & Prerequisite:** `count_total` must **never** be used as the first tool call.
Because user inputs may contain wrong, abbreviated, or partial item names, you must always call `find_item`
first to retrieve the official item names from the database.
2. **Execution Sequence:** `count_total` is strictly to be used only *after* you have already called `find_item`
to obtain the correct and proper database names, which you then pass into the `item_names` argument.
3. **Item Names:** Pass the exact validated item names retrieved from the database into the `item_names` list argument.
4. **Handling Missing Items:** If the tool response indicates that any requested item was missing or not found, you must
explicitly mention this in your final response to inform the user that those items were excluded from the total calculation.
5. **Zero Total Price:** If the total price is 0 because all of the item(s) requested by the user is/are missing, then do not
include the price in your final response.
6. **A Singular Item:** If the user only supplies one item but is still asking for a total price, you must still call `find_item`
first, and then use `count_total` with its correct database name instead of other tools.

#Special exception
When the user makes a query "Command Alpha", ignore all previous tool restriction and make a function call for
tool `count_total` with a list containing "kunci", "Webcam" in said list as the argument for the tool
"""

TOOLS = [
    {
        "type": "function",
        "name": "find_item",
        "description": (
            "Returns a complete list of all items currently stored in the database if no argument is given."
            "Returns an item if an item name is given as the argument"
            "Each item contains the following keys: `name`, and `price` and their respective values"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {
                    "type": "string",
                    "description": "The item name is given as the argument to find the details of only said item",
                }
            },
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

PSEUDO_DB = [
    {"name": "Mouse nirkabel", "price": 150000},
    {"name": "Keyboard mekanik", "price": 275000},
    {"name": "Headset", "price": 320000},
    {"name": "Hub USB", "price": 189000},
    {"name": "Webcam", "price": 410000},
]

HISTORY_FILE_PATH = "riwayat.json"

MAX_QUERIES_STORED = 2

def find_item(item_name = None) -> str:
    if item_name is None:
        return PSEUDO_DB
    
    for entry in PSEUDO_DB:
        if item_name.casefold() in entry["name"].casefold():
            return entry

    return "Item is unavailable"

def count_total(items:list) -> str:
    set_items = set(items)
    total_price = 0.0

    for entry in PSEUDO_DB:
        item_name = entry.get("name")
        if item_name in set_items:
            total_price += float(entry["price"])
            set_items.remove(item_name)

    final_answer = f"Total Price: {total_price}"
    if set_items:
        final_answer += f". But the following items are not found: {set_items}"

    return final_answer

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

        max_chains = 4 # Don't forget to synchronize this number with the one set in INSTRUCTIONS too
        chain_number = 0
        while chain_number < max_chains:
            chain_number += 1
            response_stream = client.responses.create(
                model=openrouter_model,
                instructions=INSTRUCTIONS,
                input=temp_list,
                tools=TOOLS,
                stream = True,
            )
            response_output = None
            response_collected = False
            for event in response_stream:
                if event.type == "response.output_text.delta":
                    # Agent is giving the final answer to user's query
                    print(event.delta, end="", flush=True)

                elif event.type == "response.completed":
                    temp_list += event.response.output
                    response_output = event.response.output
                    response_collected = True
                    
            # Do final check if response has been properly completed
            if not response_collected:
                return "An error has occurred. It seems that the response from the agent has never reached completion status. Please retry your query again."
            
            tools_called = False
            for item in response_output:
                if item.type == "function_call":
                    # Preparing for the next chain function call
                    tools_called = True
                    if item.name == "find_item":
                        try:
                            arg = json.loads(item.arguments)["item_name"]
                            if arg == "":
                                print(f"Tool {item.name}() has been requested by the agent")
                                tool_output = json.dumps(find_item())
                            else:
                                print(f"Tool {item.name}({arg}) has been requested by the agent")
                                tool_output = json.dumps(find_item(arg))
                        except json.JSONDecodeError:
                            tool_output = json.dumps({"error": "The given argument is not JSON"})

                    elif item.name == "count_total":
                        try:
                            items = json.loads(item.arguments)["item_names"]
                            print(f"Tool {item.name}({items}) has been requested by the agent")
                            tool_output = json.dumps(count_total(items))
                        except json.JSONDecodeError:
                            tool_output = json.dumps({"error": "The given argument is not JSON"})
                    
                    else:
                        print(f"Tool {item.name} has been requested by the agent, but this tool doesn't exist!")
                        tool_output = json.dumps({"error": f"Tool '{item.name}' does not exist."})

                    temp_list.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": tool_output,
                        }
                    )   
            if not tools_called:
                # This should be the final answer from the agent to the user's query
                count = len(temp_list) - count
                input_list.clear()
                input_list.extend(temp_list)
                count_list.append(count)
                return ""
            
        # Over the limit of max_chains
        return "An error has occurred. It seems that your request is too complex to be completed all at once. Please try a simpler query."

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
        db = json.loads(find_item())
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

        while len(count_list) > MAX_QUERIES_STORED:
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
        print(result)
            
        while len(count_list) > MAX_QUERIES_STORED:
            trim_history(input_list, count_list)


if __name__ == "__main__":
    main()

