import io
import json
import unittest
from unittest.mock import MagicMock, patch

from assistant_agent import call_ai_with_tools


class TestAPICalls(unittest.TestCase):

    def test_call_ai_with_tools_mocked(self):
        mock_client = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.type = "function_call"
        mock_tool_call.name = "count_total"
        mock_tool_call.call_id = "call_xyz_789"
        mock_tool_call.arguments = json.dumps({"list": ["Mouse nirkabel"]})

        first_response_mock = MagicMock()
        first_response_mock.output = [mock_tool_call]

        event_completed_1 = MagicMock()
        event_completed_1.type = "response.completed"
        event_completed_1.response = first_response_mock

        event_delta = MagicMock()
        event_delta.type = "response.output_text.delta"
        event_delta.delta = "Total price for Mouse nirkabel is 150.000."

        event_completed_2 = MagicMock()
        event_completed_2.type = "response.completed"
        event_completed_2.response = MagicMock(output=[])

        first_response_stream = [event_completed_1]
        second_response_stream = [event_delta, event_completed_2]

        mock_client.responses.create.side_effect = [
            first_response_stream,
            second_response_stream,
        ]

        input_list = []
        count_list = []
        user_input = "What is the total price for Mouse nirkabel?"

        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            result = call_ai_with_tools(
                mock_client, "test-model", input_list, user_input, count_list, {} 
            )

        assert "150.000" in captured_output.getvalue()
        assert mock_client.responses.create.call_count == 2
        assert len(count_list) == 1
        has_tool_output = any(
            isinstance(item, dict) and item.get("type") == "function_call_output"
            for item in input_list
        )
        assert (
            has_tool_output
        ), "The input_list should record the function_call_output response."

    def test_call_ai_add_to_cart_mocked(self):
        mock_client = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.type = "function_call"
        mock_tool_call.name = "add_to_cart"
        mock_tool_call.call_id = "call_cart_1"
        mock_tool_call.arguments = json.dumps({"name": "Headset", "amount": 2})

        first_response_mock = MagicMock()
        first_response_mock.output = [mock_tool_call]

        event_completed_1 = MagicMock()
        event_completed_1.type = "response.completed"
        event_completed_1.response = first_response_mock

        event_delta = MagicMock()
        event_delta.type = "response.output_text.delta"
        event_delta.delta = "Successfully added 2 Headset to the cart!"

        event_completed_2 = MagicMock()
        event_completed_2.type = "response.completed"
        event_completed_2.response = MagicMock(output=[])

        mock_client.responses.create.side_effect = [
            [event_completed_1],
            [event_delta, event_completed_2],
        ]

        input_list = []
        count_list = []
        cart = {}
        user_input = "Add 2 Headset to the cart"

        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            call_ai_with_tools(
                mock_client, "test-model", input_list, user_input, count_list, cart
            )

        assert "Successfully added 2 Headset" in captured_output.getvalue()
        assert mock_client.responses.create.call_count == 2
        assert "Headset" in cart
        assert cart["Headset"]["amount"] == 2

    def test_call_ai_show_cart_mocked(self):
        mock_client = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.type = "function_call"
        mock_tool_call.name = "show_cart"
        mock_tool_call.call_id = "call_cart_2"
        mock_tool_call.arguments = json.dumps({})

        first_response_mock = MagicMock()
        first_response_mock.output = [mock_tool_call]

        event_completed_1 = MagicMock()
        event_completed_1.type = "response.completed"
        event_completed_1.response = first_response_mock

        event_delta = MagicMock()
        event_delta.type = "response.output_text.delta"
        event_delta.delta = "Headset x2: Rp640000\nTotal: 640000"

        event_completed_2 = MagicMock()
        event_completed_2.type = "response.completed"
        event_completed_2.response = MagicMock(output=[])

        mock_client.responses.create.side_effect = [
            [event_completed_1],
            [event_delta, event_completed_2],
        ]

        input_list = []
        count_list = []
        cart = {"Headset": {"amount": 2, "total": 640000}}
        user_input = "Show my cart"

        captured_output = io.StringIO()
        with patch("sys.stdout", new=captured_output):
            call_ai_with_tools(
                mock_client, "test-model", input_list, user_input, count_list, cart
            )

        assert "Headset x2" in captured_output.getvalue()
        assert "Total: 640000" in captured_output.getvalue()
        assert mock_client.responses.create.call_count == 2

    def test_call_ai_direct_response_mocked(self):
        mock_client = MagicMock()
        event_completed = MagicMock()
        event_completed.type = "response.completed"
        event_completed.response = MagicMock(output=[])

        mock_client.responses.create.return_value = [event_completed]

        input_list = []
        count_list = []
        user_input = "How's the weather today?"

        result = call_ai_with_tools(
            mock_client, "test-model", input_list, user_input, count_list, {}
        )

        assert result == ""
        assert mock_client.responses.create.call_count == 1
        assert len(count_list) == 1

    def test_call_ai_chained_tool_error_mocked(self):
        mock_client = MagicMock()
        
        tool_call_1 = MagicMock()
        tool_call_1.type = "function_call"
        tool_call_1.name = "find_item"
        tool_call_1.call_id = "call_1"
        tool_call_1.arguments = json.dumps({"name": ""})

        response_mock_1 = MagicMock()
        response_mock_1.output = [tool_call_1]

        event_completed_1 = MagicMock()
        event_completed_1.type = "response.completed"
        event_completed_1.response = response_mock_1

        tool_call_2 = MagicMock()
        tool_call_2.type = "function_call"
        tool_call_2.name = "count_total"
        tool_call_2.call_id = "call_2"
        tool_call_2.arguments = json.dumps({"list": ["Mouse nirkabel"]})

        response_mock_2 = MagicMock()
        response_mock_2.output = [tool_call_2]

        event_completed_2 = MagicMock()
        event_completed_2.type = "response.completed"
        event_completed_2.response = response_mock_2

        mock_client.responses.create.side_effect = [
            [event_completed_1],
            [event_completed_2],
            [event_completed_2],
            [event_completed_2],
            [event_completed_2]
        ]

        input_list = []
        count_list = []
        user_input = "Give me a list of all items and count all of their total price"

        result = call_ai_with_tools(
            mock_client, "test-model", input_list, user_input, count_list, {}
        )

        assert "too complex" in result.lower()

    def test_input_list_unmodified_on_exception(self):
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = Exception("Network timeout")

        initial_input_list = [{"role": "user", "content": "Hello"}]
        input_list_copy = list(initial_input_list)
        count_list = []

        result = call_ai_with_tools(
            mock_client, "test-model", initial_input_list, "Test prompt", count_list, {}
        )

        assert "An error has occurred" in result
        assert initial_input_list == input_list_copy

    def test_input_list_unmodified_on_chained_tool_error(self):
        mock_client = MagicMock()
        
        tool_call_1 = MagicMock()
        tool_call_1.type = "function_call"
        tool_call_1.name = "find_item"
        tool_call_1.call_id = "call_1"
        tool_call_1.arguments = json.dumps({"name": ""})

        response_mock_1 = MagicMock()
        response_mock_1.output = [tool_call_1]

        event_completed_1 = MagicMock()
        event_completed_1.type = "response.completed"
        event_completed_1.response = response_mock_1

        tool_call_2 = MagicMock()
        tool_call_2.type = "function_call"
        tool_call_2.name = "count_total"
        tool_call_2.call_id = "call_2"
        tool_call_2.arguments = json.dumps({"list": ["Mouse nirkabel"]})

        response_mock_2 = MagicMock()
        response_mock_2.output = [tool_call_2]

        event_completed_2 = MagicMock()
        event_completed_2.type = "response.completed"
        event_completed_2.response = response_mock_2

        mock_client.responses.create.side_effect = [
            [event_completed_1],
            [event_completed_2],
            [event_completed_2],
            [event_completed_2],
            [event_completed_2]
        ]

        initial_input_list = [{"role": "user", "content": "Initial history"}]
        input_list_copy = list(initial_input_list)
        count_list = []

        result = call_ai_with_tools(
            mock_client, "test-model", initial_input_list, "Give me everything and calculate", count_list, {}
        )

        assert "too complex" in result.lower()
        assert initial_input_list == input_list_copy

if __name__ == "__main__":
    unittest.main()