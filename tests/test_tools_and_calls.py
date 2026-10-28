import json
import unittest
from unittest.mock import MagicMock
import pytest

from assistant_agent import TOOLS, PSEUDO_DB, list_items, call_ai_with_tools

class TestDotEnvLoading(unittest.TestCase):

    def test_tools_json_validity(self):
        try:
            serialized_tools = json.dumps(TOOLS)
            assert isinstance(serialized_tools, str)
            deserialized_tools = json.loads(serialized_tools)
            assert deserialized_tools == TOOLS
        except (TypeError, ValueError) as e:
            pytest.fail(f"TOOLS structure is not valid JSON serializable: {e}")

    def test_call_ai_with_tools_mocked(self):
        mock_client = MagicMock()
        mock_tool_call_item = MagicMock()
        mock_tool_call_item.type = "function_call"
        mock_tool_call_item.name = "list_items"
        mock_tool_call_item.call_id = "call_mock_123"

        first_response_mock = MagicMock()
        first_response_mock.output = [mock_tool_call_item]
        second_response_mock = MagicMock()
        second_response_mock.output_text = (
            "Here are the available items: mouse, keyboard, and webcam."
        )
        mock_client.responses.create.side_effect = [
            first_response_mock,
            second_response_mock,
        ]

        input_list = [{"role": "user", "content": "What items are in the database?"}]
        result = call_ai_with_tools(mock_client, input_list, "test-model")

        assert "Here are the available items: mouse, keyboard, and webcam." in result
        assert mock_client.responses.create.call_count == 2
        has_tool_output = any(
            isinstance(item, dict) and item.get("type") == "function_call_output"
            for item in input_list
        )
        assert has_tool_output, "The input_list should record the function_call_output response."

if __name__ == "__main__":
    unittest.main()