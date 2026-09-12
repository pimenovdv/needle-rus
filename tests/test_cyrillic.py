import json
import pytest
from needle.agent.tools import build_schema

def test_json_dumps_cyrillic():
    data = {"ключ": "значение", "тест": 123}
    encoded = json.dumps(data, ensure_ascii=False)
    assert "ключ" in encoded
    assert "значение" in encoded
    # Check no unicode escapes
    assert r"\u" not in encoded

def test_utf8_encoding_decoding():
    text = "Тестовая строка с кириллицей"
    encoded = text.encode("utf-8")
    assert encoded.decode("utf-8") == text

def test_tool_arguments_cyrillic():
    def mock_tool(аргумент: str, число: int = 5):
        """
        Тестовый инструмент.

        args:
            аргумент: Строковый аргумент.
            число: Числовой аргумент.
        """
        pass

    schema = build_schema(mock_tool)
    assert schema["name"] == "mock_tool"
    assert "аргумент" in schema["parameters"]["properties"]
    assert "число" in schema["parameters"]["properties"]
    assert schema["parameters"]["properties"]["аргумент"]["description"] == "Строковый аргумент."
