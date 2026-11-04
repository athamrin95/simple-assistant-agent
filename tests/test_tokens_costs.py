import unittest
from unittest.mock import patch, MagicMock
from assistant_agent_token import call_ai_with_tools, calculate_tokens_cost

class TestTokenUsageAndCost(unittest.TestCase):

    def test_call_ai_with_tools_token_tracking(self):
        mock_client = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.type = "function_call"
        mock_tool_call.name = "list_items"
        mock_tool_call.call_id = "call_1"
        first_response_mock = MagicMock()
        first_response_mock.output = [mock_tool_call]
        first_response_mock.usage = MagicMock(input_tokens=100, output_tokens=20)
        event_delta = MagicMock()
        event_delta.type = "response.output_text.delta"
        event_delta.delta = "Daftar barang..."
        event_completed = MagicMock()
        event_completed.type = "response.completed"
        event_completed.response = MagicMock(
            output=[], 
            usage=MagicMock(input_tokens=150, output_tokens=50)
        )
        second_response_stream = [event_delta, event_completed]
        mock_client.responses.create.side_effect = [
            first_response_mock,
            second_response_stream,
        ]
        input_list = []
        count_list = []
        user_input = "Show me the list of items"
        with patch("assistant_agent_token.calculate_tokens_cost", return_value=1.5):
            result = call_ai_with_tools(
                mock_client, input_list, user_input, count_list, "test-model"
            )

        assert "Total input tokens: 250" in result
        assert "Total output tokens: 70" in result
        assert "Approximate cost: Rp.1.5" in result

    @patch("assistant_agent_token.requests.get")
    def test_calculate_tokens_cost(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "test-model",
                    "pricing": {
                        "prompt": "0.000001",     # 1 per million per token
                        "completion": "0.000002"  # 2 per million per token
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # 1,000 input tokens & 1,000 output tokens
        # Input cost: (1000 / 1_000_000) * (0.000001 * 1_000_000) = 0.001
        # Output cost: (1000 / 1_000_000) * (0.000002 * 1_000_000) = 0.002
        # Base cost = 0.003 -> Converted to Rupiah (* 18_000) = 54.0
        cost = calculate_tokens_cost(1000, 1000, "test-model")
        self.assertAlmostEqual(cost, 54.0)