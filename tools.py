
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
            "required": ["list"],
        },
    },
    {
        "type": "function",
        "name": "add_to_cart",
        "description": (
            "Add the given item name and amount to the cart."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The item name to be added to the cart",
                },
                "amount": {
                    "type": "integer",
                    "description": "The amount of item to be added to the cart",
                },
            },
            "required": ["name", "amount"],
        },
    },
    {
        "type": "function",
        "name": "show_cart",
        "description": (
            "Show the item, amount, price, and all item total price from the cart."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
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

def add_to_cart(db:list, cart:dict, name:str, amount:int):
    if amount < 1 or amount > 10:
        return {"error": "The given amount has exceeded the set limit or is set below it."}

    ori_amount = amount
    # Strict name check enforced
    for entry in db:
        if name == entry["name"]:
            # Check if item already exist in cart
            if entry["name"] in cart:
                amount = cart[entry["name"]]["amount"] + amount
                
            cart[entry["name"]] = {"amount": amount, "total": amount*entry["price"]}
            return f"Successfully added {ori_amount} {entry["name"]} to the cart!"

    return {"error": "The given item name is not found in the database."}

def show_cart(cart:dict):
    total = 0
    string = ""
    for key, values in cart.items():
        string += f"{key} x{values["amount"]}: Rp{values["total"]}\n"
        total += values["total"]

    if string == "":
        return "The cart is empty."

    return string + f"Total: {total}"

def tool_finder(db:list, tool_name:str, args:str, cart:dict):
    try:
        args_dict = json.loads(args)
    except JSONDecodeError:
        return {"error": "The given argument is not JSON"}
    except Exception as e:
        raise Exception(e)

    if tool_name == "find_item":
        arg = args_dict["name"]
        print(f"Tool {tool_name}({arg}) has been requested by the agent")
        if arg is None or arg == "":
            return find_item(db)
        else:
            return find_item(db, arg)

    elif tool_name == "count_total":
        arg = args_dict["list"]
        print(f"Tool {tool_name}({arg}) has been requested by the agent")
        return count_total(db, arg)

    elif tool_name == "add_to_cart":
        arg_name = args_dict["name"]
        arg_amount = args_dict["amount"]
        print(f"Tool {tool_name}({arg_name}, {arg_amount}) has been requested by the agent")
        return add_to_cart(db, cart, arg_name, arg_amount)
    
    elif tool_name == "show_cart":
        print(f"Tool {tool_name}() has been requested by the agent")
        return show_cart(cart)

    else:
        print(f"Tool {tool_name} has been requested by the agent, but this tool does not exist!")
        return {"error": f"Tool `{tool_name}` does not exist."}