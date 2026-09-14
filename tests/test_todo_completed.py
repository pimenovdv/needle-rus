def test_todo_all_checked():
    with open("TODO.md", "r", encoding="utf-8") as f:
        content = f.read()
        assert "[ ]" not in content, "There are still unresolved tasks in TODO.md"
