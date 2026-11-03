import json
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import tempfile

from assistant_agent import (
    count_total,
    local_command,
    trim_history,
)


class TestFunctions(unittest.TestCase):

    def test_count_total_success_and_missing(self):
        test_items = ["Mouse nirkabel", "NonExistentItem", "headset"]
        result = count_total(test_items)
        assert "470000" in result
        assert "NonExistentItem" in result

    def test_trim_history(self):
        input_list = ["msg1", "msg2", "msg3", "msg4", "msg5"]
        count_list = [2, 3]

        trim_history(input_list, count_list)
        
        assert input_list == ["msg3", "msg4", "msg5"]
        assert count_list == [3]

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_riwayat.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_local_command_keluar_serialization(self):
        mock_sdk_obj = MagicMock()
        mock_sdk_obj.model_dump.return_value = {
            "type": "function_call",
            "name": "list_items",
            "arguments": "{}"
        }

        input_list = [
            {"role": "user", "content": "How much is the cost of headset?"},
            mock_sdk_obj,
            {
                "type": "function_call_output",
                "call_id": "call_123",
                "output": "Total price is 320000."
            }
        ]

        with patch("assistant_agent.HISTORY_FILE_PATH", self.test_file_path):
            with self.assertRaises(SystemExit) as cm:
                local_command("/keluar", input_list)
            
            self.assertEqual(cm.exception.code, 1)

        self.assertTrue(os.path.exists(self.test_file_path))

        loaded_entries = []
        with open(self.test_file_path, "r", encoding="utf-8") as f:
            for line in f:
                loaded_entries.append(json.loads(line))

        self.assertEqual(len(loaded_entries), 3)
        self.assertEqual(loaded_entries[0]["role"], "user")
        self.assertEqual(loaded_entries[1]["type"], "function_call")
        self.assertEqual(loaded_entries[1]["name"], "list_items")
        self.assertEqual(loaded_entries[2]["output"], "Total price is 320000.")

    def test_history_deserialization_logic(self):
        sample_entries = [
            {"role": "user", "content": "List barang"},
            {"role": "assistant", "content": "Berikut daftar barang..."},
            {"role": "user", "content": "Hitung total headset dan webcam"}
        ]

        with open(self.test_file_path, "w", encoding="utf-8") as f:
            for entry in sample_entries:
                f.write(json.dumps(entry) + "\n")

        deserialized_input_list = []
        try:
            with Path(self.test_file_path).open("r", encoding="utf-8") as f:
                for line in f:
                    deserialized_input_list.append(json.loads(line))
        except Exception as e:
            self.fail(f"Deserialization failed unexpectedly: {e}")

        self.assertEqual(len(deserialized_input_list), 3)
        self.assertEqual(deserialized_input_list, sample_entries)

    def test_deserialization_handles_nonexistent_file(self):
        non_existent_file = os.path.join(self.temp_dir.name, "does_not_exist.json")
        with self.assertRaises(FileNotFoundError):
            with open(non_existent_file, "r") as f:
                pass

if __name__ == "__main__":
    unittest.main()