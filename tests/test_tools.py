import json
import unittest

import pytest

from tools import count_total, find_item, add_to_cart, show_cart, tool_finder, TOOLS
from assistant_agent import PSEUDO_DB

class TestTools(unittest.TestCase):

    def test_tools_json_validity(self):
        try:
            serialized_tools = json.dumps(TOOLS)
            assert isinstance(serialized_tools, str)
            deserialized_tools = json.loads(serialized_tools)
            assert deserialized_tools == TOOLS
        except (TypeError, ValueError) as e:
            pytest.fail(f"TOOLS structure is not valid JSON serializable: {e}")

    def test_count_total_success_and_missing(self):
        test_items = ["Mouse nirkabel", "NonExistentItem"]
        result = count_total(PSEUDO_DB, test_items)
        
        assert "NonExistentItem" in result
        assert "150" in result

    def test_find_item_all(self):
        result = str(find_item(PSEUDO_DB))

        assert all(item in result for item in ["Mouse nirkabel", "Keyboard mekanik", "Webcam", "Headset", "Hub USB"])

    def test_find_item_one(self):
        result = str(find_item(PSEUDO_DB, "Mouse nirkabel"))
        result_partial_name = str(find_item (PSEUDO_DB, "usb"))

        assert "Mouse" and "150" in result
        assert "Webcam" not in result
        assert "Hub USB" in result_partial_name

    def test_find_item_missing(self):
        result = str(find_item(PSEUDO_DB, "NonExistantItem"))

        assert "unavailable" in result

    def test_find_item_extra_cases(self):
        res_case = find_item(PSEUDO_DB, "webcam")
        self.assertIsInstance(res_case, dict)
        self.assertEqual(res_case["name"], "Webcam")
        self.assertEqual(res_case["price"], 410000)

        res_mid = find_item(PSEUDO_DB, "mekanik")
        self.assertIsInstance(res_mid, dict)
        self.assertEqual(res_mid["name"], "Keyboard mekanik")

    def test_add_to_cart_success(self):
        cart = {}
        result = add_to_cart(PSEUDO_DB, cart, "Mouse nirkabel", 2)
        self.assertIn("Successfully added", result)
        self.assertEqual(cart["Mouse nirkabel"]["amount"], 2)
        self.assertEqual(cart["Mouse nirkabel"]["total"], 300000)

    def test_add_to_cart_accumulate(self):
        cart = {"Mouse nirkabel": {"amount": 1, "total": 150000}}
        result = add_to_cart(PSEUDO_DB, cart, "Mouse nirkabel", 3)
        self.assertIn("Successfully added", result)
        self.assertEqual(cart["Mouse nirkabel"]["amount"], 4)
        self.assertEqual(cart["Mouse nirkabel"]["total"], 600000)

    def test_add_to_cart_amount_limits(self):
        cart = {}
        res_low = add_to_cart(PSEUDO_DB, cart, "Webcam", 0)
        self.assertIn("error", res_low)
        
        res_high = add_to_cart(PSEUDO_DB, cart, "Webcam", 11)
        self.assertIn("error", res_high)

    def test_add_to_cart_item_not_found(self):
        cart = {}
        result = add_to_cart(PSEUDO_DB, cart, "NonExistentItem", 2)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "The given item name is not found in the database.")

    def test_show_cart_empty(self):
        cart = {}
        result = show_cart(cart)
        self.assertEqual(result, "The cart is empty.")

    def test_show_cart_with_items(self):
        cart = {
            "Mouse nirkabel": {"amount": 2, "total": 300000},
            "Webcam": {"amount": 1, "total": 410000}
        }
        result = show_cart(cart)
        self.assertIn("Mouse nirkabel x2: Rp300000", result)
        self.assertIn("Webcam x1: Rp410000", result)
        self.assertIn("Total: 710000", result)

    def test_tool_finder_find_item_no_args(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": None}), {})

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(PSEUDO_DB))

    def test_tool_finder_find_item_empty_string_arg(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": ""}), {})

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(PSEUDO_DB))

    def test_tool_finder_find_item_valid_arg(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": "Headset"}), {})

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("name"), "Headset")
        self.assertEqual(result.get("price"), 320000)

    def test_tool_finder_find_item_partial_or_case_insensitive(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": "keyboard"}), {})

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("name"), "Keyboard mekanik")

    def test_tool_finder_find_item_missing(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": "Smartwatch"}), {})

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Item is unavailable")

    def test_tool_finder_count_total(self):
        items_to_count = ["Mouse nirkabel", "Hub USB"]
        result = tool_finder(PSEUDO_DB, "count_total", json.dumps({"list": items_to_count}), {})

        self.assertIsInstance(result, str)
        self.assertIn("339000.0", result)

    def test_tool_finder_add_to_cart(self):
        cart = {}
        result = tool_finder(PSEUDO_DB, "add_to_cart", json.dumps({"name": "Headset", "amount": 3}), cart)
        self.assertIn("Successfully added", result)
        self.assertEqual(cart["Headset"]["amount"], 3)

    def test_tool_finder_show_cart(self):
        cart = {"Headset": {"amount": 3, "total": 960000}}
        result = tool_finder(PSEUDO_DB, "show_cart", json.dumps({}), cart)
        self.assertIn("Headset x3", result)
        self.assertIn("Total: 960000", result)

    def test_tool_finder_invalid_json(self):
        result = tool_finder(PSEUDO_DB, "find_item", "not-json-string", {})

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "The given argument is not JSON")

    def test_tool_finder_unknown_tool(self):
        result = tool_finder(PSEUDO_DB, "invalid_tool_name", json.dumps({"arg": "some_arg"}), {})
        
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("does not exist", result["error"])

if __name__ == "__main__":
    unittest.main()