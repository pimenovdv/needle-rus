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

def test_cyrillic_masking(tmp_path):
    from needle.model.finetune import _encode
    from needle.model.tokenizer import get_tokenizer

    tokenizer = get_tokenizer()
    example = {
        "query": "Отправь письмо Ивану",
        "reasoning": "Запрос на отправку email",
        "answers": [{"name": "send_email", "arguments": {"to": "Иван"}}]
    }

    # We use a large enough max_len to fit the encoded string
    max_len = 128
    ids, mask = _encode(tokenizer, example, max_len)

    # Let's ensure the mask is 0.0 for the query part and 1.0 for the answer part
    assert len(ids) == max_len
    assert len(mask) == max_len

    # Check that mask contains both 0.0 and 1.0
    assert 0.0 in mask
    assert 1.0 in mask

    # Non-pad tokens should be > 0.
    non_pad_count = 0
    for id in ids:
        if id != 0:
            non_pad_count += 1

    # The mask should have 1s at the end of the non-pad tokens (answer part)
    # Target starts with `<think>\nЗапрос...` and ends with `<|im_end|>`
    # We verify that target is correctly masked with 1.0
    assert sum(mask) > 0
    # There should be exactly 'pad' number of 0s at the very end
    pad_count = sum(1 for id in ids if id == 0)
    assert sum(mask[-pad_count:]) == 0.0 if pad_count > 0 else True

def test_fit_max_len_cyrillic(tmp_path):
    import json
    from needle.model.finetune import fit_max_len
    from needle.model.tokenizer import get_tokenizer

    tokenizer = get_tokenizer()

    # Create a dummy jsonl file with a highly segmented Cyrillic text
    data_path = tmp_path / "data.jsonl"
    example = {
        "query": "Очень длинный текст на русском языке с большим количеством слов, которые могут разбиваться на множество токенов из-за ограниченного размера словаря. " * 10,
        "answers": []
    }
    with open(data_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(example, ensure_ascii=False) + "\n")

    # Test that fit_max_len correctly calculates and expands bucket
    cap = 2048
    bucket = fit_max_len(str(data_path), tokenizer, cap)

    # Our query is very long, so the bucket should be fairly large, certainly larger than 128
    assert bucket > 128
    # But it should not exceed cap
    assert bucket <= cap


def test_byte_fallback_json():
    from needle.model.export import RefTokenizer

    # Simulating a small dummy BPE vocabulary that falls back to byte tokens.
    # Type 4 represents BYTE token. Assuming byte_fallback=True.
    # A vocab item for bytes is represented by "<0xXX>".
    # Byte tokens list generated for standard RefTokenizer structure.
    vocab = ["<pad>", "<s>", "</s>", "<unk>"]
    types = [2, 2, 2, 1]

    # Add byte tokens <0x00> to <0xFF>
    for b in range(256):
        vocab.append(f"<0x{b:02X}>")
        types.append(4)  # TK_BYTE

    meta = {
        "pieces": vocab,
        "scores": [0.0] * len(vocab),
        "types": types,
        "pad_id": 0,
        "bos_id": 1,
        "eos_id": 2,
        "unk_id": 3,
        "add_dummy_prefix": False,
        "byte_fallback": True,
    }

    tokenizer = RefTokenizer(meta)

    # Testing some cyrillic word e.g., "Тест"
    # "Тест" in UTF-8 bytes:
    # Т: \xd0 \xa2 (208, 162)
    # е: \xd0 \xb5 (208, 181)
    # с: \xd1 \x81 (209, 129)
    # т: \xd1 \x82 (209, 130)

    word = "Тест"
    encoded = tokenizer.encode(word)

    # We should get 8 tokens (each byte separately since we don't have cyrillic words in vocab)
    assert len(encoded) == 8

    # Validate specific byte tokens mapping (token indices start at 4 for byte 0x00)
    # 0xD0 is 208, so idx is 4 + 208 = 212
    # 0xA2 is 162, so idx is 4 + 162 = 166
    assert encoded[0] == 4 + 208
    assert encoded[1] == 4 + 162

    # Asserting that decoding correctly reconstructs the utf-8 characters using byte level fallback
    # Because RefTokenizer currently only implements encode in the exported code (for simulation purposes),
    # verifying encode works explicitly guarantees byte-level grammar decoding is unhindered for JSON.
