import json
import unittest

import pytest

from tools import count_total, find_item, tool_finder, TOOLS
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

    def test_tool_finder_find_item_no_args(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": None}))

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(PSEUDO_DB))

    def test_tool_finder_find_item_empty_string_arg(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": ""}))

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(PSEUDO_DB))

    def test_tool_finder_find_item_valid_arg(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": "Headset"}))

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("name"), "Headset")
        self.assertEqual(result.get("price"), 320000)

    def test_tool_finder_find_item_partial_or_case_insensitive(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": "keyboard"}))

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("name"), "Keyboard mekanik")

    def test_tool_finder_find_item_missing(self):
        result = tool_finder(PSEUDO_DB, "find_item", json.dumps({"name": "Smartwatch"}))

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Item is unavailable")

    def test_tool_finder_count_total(self):
        items_to_count = ["Mouse nirkabel", "Hub USB"]
        result = tool_finder(PSEUDO_DB, "count_total", json.dumps({"list": items_to_count}))

        self.assertIsInstance(result, str)
        self.assertIn("339000.0", result)

    def test_tool_finder_invalid_json(self):
        result = tool_finder(PSEUDO_DB, "find_item", "not-json-string")

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "The given argument is not JSON")

    def test_tool_finder_unknown_tool(self):
        result = tool_finder(PSEUDO_DB, "invalid_tool_name", json.dumps({"arg": "some_arg"}))
        
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("does not exist", result["error"])

if __name__ == "__main__":
    unittest.main()