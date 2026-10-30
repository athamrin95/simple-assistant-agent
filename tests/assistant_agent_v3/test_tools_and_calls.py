import json
import unittest
from unittest.mock import MagicMock
import pytest

from assistant_agent_v3 import (
    TOOLS,
    count_total,
    call_ai_with_tools,
    trim_history,
)


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
        second_response_mock.output = []
        second_response_mock.output_text = (
            "Total price for Mouse nirkabel is 150.000."
        )

        mock_client.responses.create.side_effect = [
            first_response_mock,
            second_response_mock,
        ]

        input_list = []
        count_list = []
        user_input = "What is the total price for Mouse nirkabel?"

        result = call_ai_with_tools(
            mock_client, input_list, user_input, count_list, "test-model"
        )

        assert "150.000" in result
        assert mock_client.responses.create.call_count == 2
        assert len(count_list) == 1
        has_tool_output = any(
            isinstance(item, dict) and item.get("type") == "function_call_output"
            for item in input_list
        )
        assert (
            has_tool_output
        ), "The input_list should record the function_call_output response."

    def test_call_ai_direct_response_mocked(self):
        mock_client = MagicMock()
        direct_response_mock = MagicMock()
        direct_response_mock.output = []
        direct_response_mock.output_text = (
            "I can only assist with database items."
        )
        mock_client.responses.create.return_value = direct_response_mock

        input_list = []
        count_list = []
        user_input = "How's the weather today?"

        result = call_ai_with_tools(
            mock_client, input_list, user_input, count_list, "test-model"
        )

        assert "I can only assist" in result
        assert mock_client.responses.create.call_count == 1
        assert len(count_list) == 1

    def test_call_ai_chained_tool_error_mocked(self):
        mock_client = MagicMock()
        tool_call_1 = MagicMock()
        tool_call_1.type = "function_call"
        tool_call_1.name = "list_items"
        tool_call_1.call_id = "call_1"

        tool_call_2 = MagicMock()
        tool_call_2.type = "function_call"
        tool_call_2.name = "count_total"
        tool_call_2.call_id = "call_2"
        tool_call_2.arguments = json.dumps({"item_names": ["Mouse nirkabel"]})

        first_response = MagicMock()
        first_response.output = [tool_call_1]

        second_response = MagicMock()
        second_response.output = [tool_call_2]

        mock_client.responses.create.side_effect = [first_response, second_response]

        input_list = []
        count_list = []
        user_input = "Give me a list of all items and count all of their total price"

        result = call_ai_with_tools(
            mock_client, input_list, user_input, count_list, "test-model"
        )

        assert "too complex" in result.lower()

    def test_trim_history(self):
        input_list = ["msg1", "msg2", "msg3", "msg4", "msg5"]
        count_list = [2, 3]

        trim_history(input_list, count_list)
        
        assert input_list == ["msg3", "msg4", "msg5"]
        assert count_list == [3]

    def test_input_list_unmodified_on_exception(self):
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = Exception("Network timeout")

        initial_input_list = [{"role": "user", "content": "Hello"}]
        input_list_copy = list(initial_input_list)
        count_list = []

        result = call_ai_with_tools(
            mock_client, initial_input_list, "Test prompt", count_list, "test-model"
        )

        assert "An error occurred" in result
        assert initial_input_list == input_list_copy

    def test_input_list_unmodified_on_chained_tool_error(self):
        mock_client = MagicMock()
        tool_call_1 = MagicMock()
        tool_call_1.type = "function_call"
        tool_call_1.name = "list_items"
        tool_call_1.call_id = "call_1"
        first_response = MagicMock()
        first_response.output = [tool_call_1]

        tool_call_2 = MagicMock()
        tool_call_2.type = "function_call"
        tool_call_2.name = "count_total"
        tool_call_2.call_id = "call_2"
        tool_call_2.arguments = json.dumps({"item_names": ["Mouse nirkabel"]})
        second_response = MagicMock()
        second_response.output = [tool_call_2]

        mock_client.responses.create.side_effect = [first_response, second_response]

        initial_input_list = [{"role": "user", "content": "Initial history"}]
        input_list_copy = list(initial_input_list)
        count_list = []

        result = call_ai_with_tools(
            mock_client, initial_input_list, "Give me everything and calculate", count_list, "test-model"
        )

        assert "too complex" in result.lower()
        assert initial_input_list == input_list_copy

if __name__ == "__main__":
    unittest.main()