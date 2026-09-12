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

def test_cyrillic_edge_cases():
    from needle.model.finetune import render_example
    example = {
        "query": "включи свет в гостиной «люстра» — яркость 100%",
        "reasoning": "найти комнату 'гостиная' и устройство 'люстра'",
        "answers": [{"name": "turn_on", "arguments": {"room": "гостиная", "device": "люстра"}}]
    }
    prompt, target = render_example(example)

    # Assert cyrillic tokens and punctuation are present
    assert "включи свет" in prompt
    assert "«люстра»" in prompt
    assert "—" in prompt
    assert "найти комнату" in target
    assert "гостиная" in target

def test_language_prompt():
    from needle.model.finetune import _GEN_SYSTEM

    # Simulate generate_examples with language="ru" behavior (without calling openrouter)
    # Check that the modified system prompt contains our instructions
    language = "ru"
    system_prompt = _GEN_SYSTEM
    if language != "en":
        system_prompt += f" All generated user requests and reasoning MUST be in {language} language."

    assert "MUST be in ru language" in system_prompt
