import json
import unittest
from unittest.mock import MagicMock
import pytest

from assistant_agent_v2 import TOOLS, count_total, call_ai_with_tools

class TestToolsAndCalls(unittest.TestCase):

    def test_tools_json_validity(self):
        try:
            serialized_tools = json.dumps(TOOLS)
            assert isinstance(serialized_tools, str)
            deserialized_tools = json.loads(serialized_tools)
            assert deserialized_tools == TOOLS
        except (TypeError, ValueError) as e:
            pytest.fail(f"TOOLS structure is not valid JSON serializable: {e}")

    def test_count_total_success_and_missing(self):
        test_items = ["Mouse nirkabel", "NonExistentItem", "headset"]
        result = count_total(test_items)
        assert "470000" in result
        assert "NonExistentItem" in result

    def test_call_ai_with_tools_mocked(self):
        mock_client = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.type = "function_call"
        mock_tool_call.name = "count_total"
        mock_tool_call.call_id = "call_xyz_789"
        mock_tool_call.arguments = json.dumps({"item_names": ["Mouse nirkabel"]})

        first_response_mock = MagicMock()
        first_response_mock.output = [mock_tool_call]
        second_response_mock = MagicMock()
        second_response_mock.output_text = "The total price for the Mouse nirkabel is 150,000."
        mock_client.responses.create.side_effect = [
            first_response_mock,
            second_response_mock,
        ]

        input_list = [{"role": "user", "content": "How much is the Mouse nirkabel?"}]
        result = call_ai_with_tools(mock_client, input_list, "test-model")

        assert "150,000" in result
        assert mock_client.responses.create.call_count == 2
        has_tool_output = any(
            isinstance(item, dict) and item.get("type") == "function_call_output"
            for item in input_list
        )
        assert has_tool_output, "The input_list should record the function_call_output response."

if __name__ == "__main__":
    unittest.main()