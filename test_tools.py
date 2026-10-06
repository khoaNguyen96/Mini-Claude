# test_tools.py
# Direct tests for the Chapter 2 tools. No model or API key needed.
# Run:  python -m unittest test_tools -v
import os
import tempfile
import unittest

from tools import execute_tool


class ToolTests(unittest.TestCase):
    def setUp(self):
        # Every test runs inside a throwaway directory.
        self._old = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._old)
        self._tmp.cleanup()

    def test_write_then_read(self):
        out = execute_tool("write_file", {"file_path": "sub/notes.txt", "content": "remember-this"})
        self.assertIn("Successfully wrote to sub/notes.txt (1 lines)", out)  # parent dir auto-created
        self.assertEqual(execute_tool("read_file", {"file_path": "sub/notes.txt"}), "   1 | remember-this")

    def test_read_missing_file(self):
        self.assertTrue(execute_tool("read_file", {"file_path": "nope.txt"}).startswith("Error reading file"))

    def test_edit_unique(self):
        execute_tool("write_file", {"file_path": "a.txt", "content": "hello world"})
        out = execute_tool("edit_file", {"file_path": "a.txt", "old_string": "world", "new_string": "there"})
        self.assertEqual(out, "Successfully edited a.txt")
        self.assertIn("hello there", execute_tool("read_file", {"file_path": "a.txt"}))

    def test_edit_not_found(self):
        execute_tool("write_file", {"file_path": "a.txt", "content": "hello"})
        out = execute_tool("edit_file", {"file_path": "a.txt", "old_string": "zzz", "new_string": "x"})
        self.assertEqual(out, "Error: old_string not found in a.txt")

    def test_edit_not_unique(self):
        execute_tool("write_file", {"file_path": "a.txt", "content": "x x"})
        out = execute_tool("edit_file", {"file_path": "a.txt", "old_string": "x", "new_string": "y"})
        self.assertEqual(out, "Error: old_string found 2 times in a.txt. Must be unique.")
        # file must be untouched after a refused edit
        self.assertIn("x x", execute_tool("read_file", {"file_path": "a.txt"}))

    def test_list_files(self):
        execute_tool("write_file", {"file_path": "d/one.py", "content": ""})
        execute_tool("write_file", {"file_path": "d/two.txt", "content": ""})
        out = execute_tool("list_files", {"pattern": "**/*.py"})
        self.assertIn("one.py", out)
        self.assertNotIn("two.txt", out)
        self.assertEqual(execute_tool("list_files", {"pattern": "*.zzz"}), "No files found matching the pattern.")

    def test_grep(self):
        execute_tool("write_file", {"file_path": "a.txt", "content": "alpha\nbeta"})
        self.assertIn("a.txt:2:beta", execute_tool("grep_search", {"pattern": "beta"}))
        self.assertEqual(execute_tool("grep_search", {"pattern": "gamma"}), "No matches found.")

    def test_shell(self):
        self.assertEqual(execute_tool("run_shell", {"command": "echo hi"}).strip(), "hi")
        self.assertEqual(execute_tool("run_shell", {"command": "true"}), "(no output)")
        out = execute_tool("run_shell", {"command": "echo oops >&2; exit 3"})
        self.assertIn("Command failed (exit 3)", out)
        self.assertIn("Stderr: oops", out)

    def test_unknown_tool(self):
        self.assertEqual(execute_tool("bogus", {}), "Unknown tool: bogus")


if __name__ == "__main__":
    unittest.main()