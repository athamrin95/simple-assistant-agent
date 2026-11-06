
import json
from json import JSONDecodeError

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
                "name": {
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
                "list": {
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

def find_item(db:list, item_name = None):
    if item_name is None:
        return db
    
    for entry in db:
        if item_name.casefold() in entry["name"].casefold():
            return entry

    return {"error": "Item is unavailable"}

def count_total(db:list, items:list) -> str:
    set_items = set(items)
    total_price = 0.0

    for entry in db:
        item_name = entry.get("name")
        if item_name in set_items:
            total_price += float(entry["price"])
            set_items.remove(item_name)

    final_answer = f"Total Price: {total_price}"
    if set_items:
        final_answer += f". But the following items are not found: {set_items}"

    return final_answer

def tool_finder(db:list, tool_name:str, args:str):
    # This will need to be changed once we're handling tools with multiple or zero arguments.
    # Currently all our tools only have one argument.
    try:
        args_dict = json.loads(args)
        first_key = next(iter(args_dict))
        arg = args_dict[first_key]
        print(f"Tool {tool_name}({arg}) has been requested by the agent")

    except JSONDecodeError:
        return {"error": "The given argument is not JSON"}
    
    except Exception as e:
        raise Exception(e)

    if tool_name == "find_item":
        if arg is None or arg == "":
            return find_item(db)
        else:
            return find_item(db, arg)

    elif tool_name == "count_total":
        return count_total(db, arg)

    else:
        print("But this tool does not exist!")
        return {"error": f"Tool `{tool_name}` does not exist."}