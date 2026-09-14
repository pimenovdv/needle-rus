import datetime
import json

import pydantic
import pytest


class _Stub:
    def __init__(self):
        self.envelopes = []
        self.calls = []

    def needle_init(self, system, tools, index):
        self.calls.append("init")
        return 0

    def needle_load(self, blob, size):
        return 0

    def needle_complete(self, text, *args):
        self.calls.append(("complete", text.decode("utf-8")))
        buffer = args[-2]
        envelope = self.envelopes.pop(0) if len(self.envelopes) > 1 else self.envelopes[0]
        buffer.value = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        return 0

    def needle_reset(self):
        self.calls.append("reset")


@pytest.fixture
def stub(monkeypatch):
    import needle

    engine = _Stub()
    monkeypatch.setattr(needle, "_lib", lambda generation=2: engine)
    monkeypatch.setattr(needle, "_library_path", lambda generation=2: "/tmp/libneedle2")
    monkeypatch.setattr(needle, "_active", {})
    return engine


class Invoice(pydantic.BaseModel):
    vendor: str
    due_date: datetime.date


def _call(due_date, name="Invoice"):
    return {"type": "call", "confidence": 0.9,
            "function_calls": [{"name": name,
                                "arguments": {"vendor": "Acme", "due_date": due_date}}]}


def test_complete_flags_call_dates_that_contradict_the_input(stub):
    import needle

    stub.envelopes = [_call("2026-09-05")]
    agent = needle.Needle(tools=[Invoice])
    response = agent.complete("Send an invoice to Acme due on 5th September 2031")

    assert response["validation"]["ungrounded"] == ["Invoice.due_date"]


def test_complete_leaves_grounded_dates_alone(stub):
    import needle

    stub.envelopes = [_call("2031-09-05")]
    agent = needle.Needle(tools=[Invoice])
    response = agent.complete("Send an invoice to Acme due on 5th September 2031")

    assert "validation" not in response


def test_input_without_a_year_is_not_checked(stub):
    import needle

    stub.envelopes = [_call("2026-09-05")]
    agent = needle.Needle(tools=[Invoice])
    response = agent.complete("Send Acme an invoice due next Friday")

    assert "validation" not in response


def test_run_refuses_ungrounded_calls_unless_strict_is_off(stub):
    import needle

    stub.envelopes = [_call("2026-09-05"), {"type": "respond", "function_calls": []}]
    agent = needle.Needle(tools=[Invoice])
    response = agent.run("Send an invoice to Acme due on 5th September 2031")
    assert len(response["results"]) == 1
    assert "ungrounded due_date" in response["results"][0].get("error", "").lower()

    stub.envelopes = [_call("2026-09-05"), {"type": "respond", "function_calls": []}]
    agent.reset()
    response = agent.run("Send an invoice to Acme due on 5th September 2031", strict=False)
    assert response["results"][0].due_date == datetime.date(2026, 9, 5)


def test_system_facts_license_relative_dates(stub):
    import needle

    stub.envelopes = [_call("2026-07-22")]
    agent = needle.Needle(tools=[Invoice], system="date: 2026-07-21 Tue 14:30")
    response = agent.complete("invoice Acme tomorrow for the 2019 reunion")

    assert "validation" not in response


def test_years_carry_across_turns_until_reset(stub):
    import needle

    stub.envelopes = [_call("2031-09-05")]
    agent = needle.Needle(tools=[Invoice])
    assert "validation" not in agent.complete("bill Acme on 5th September 2031")
    assert "validation" not in agent.complete(json.dumps({"id": 42, "since": "2019-03-01"}, ensure_ascii=False))

    agent.reset()
    response = agent.complete("customer since March 2019, bill them")
    assert response["validation"]["ungrounded"] == ["Invoice.due_date"]


def test_engine_reported_fabrications_are_kept_and_block_execution(stub):
    import needle

    envelope = _call("2031-09-05")
    envelope["validation"] = {"ungrounded": ["Invoice.vendor"]}
    stub.envelopes = [envelope, {"type": "respond", "function_calls": []}]
    agent = needle.Needle(tools=[Invoice])
    response = agent.run("bill someone on 5th September 2031")

    assert len(response["results"]) == 1
    assert "ungrounded vendor" in response["results"][0].get("error", "").lower()

    # Also verify that the string passed to complete has the ungrounded error
    last_call_json = json.loads(stub.calls[-1][1])
    assert len(last_call_json) == 1
    assert "ungrounded vendor" in last_call_json[0].get("error", "").lower()
