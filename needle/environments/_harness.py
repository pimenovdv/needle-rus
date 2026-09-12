import json
import os

import needle

_agents = {}


def agent_for(module):
    key = module.__name__
    if key not in _agents:
        os.environ.setdefault("NEEDLE_STRICT_VALIDATE", "1")
        _agents[key] = needle.Needle(tools=module.TOOLS, system=module.SYSTEM)
    return _agents[key]


def run_tests(module, min_confidence=0.0, verbose=True):
    """Run an environment's frozen acceptance suite against the shipped engine.
    The default scores raw model output; passing e.g. min_confidence=0.4 applies
    the production contract (act on a call only at or above the threshold,
    otherwise treat it as a refusal)."""
    agent = agent_for(module)
    failures, critical_failures = [], []
    for case in module.TEST_CASES:
        agent.reset()
        response = agent.complete(case["query"])
        got = response.get("function_calls") or []
        if got and response.get("confidence", 0.0) < min_confidence:
            got = []
        want = case["calls"]

        def _fuzzy_match(g, w):
            if isinstance(w, dict) and isinstance(g, dict):
                return len(g) == len(w) and all(k in g and _fuzzy_match(g[k], w[k]) for k in w)
            if isinstance(w, list) and isinstance(g, list):
                return len(g) == len(w) and all(_fuzzy_match(i, j) for i, j in zip(g, w))
            if isinstance(w, str) and isinstance(g, str):
                return w.lower() in g.lower() or g.lower() in w.lower()
            return g == w

        ok = got == want or (len(got) == len(want) and all(
            any(_fuzzy_match(g, w) for g in got) for w in want
        ))
        if not ok:
            failures.append(case)
            if case.get("critical"):
                critical_failures.append(case)
            if verbose:
                print(f"FAIL [{case['category']}] {case['query']}")
                print(f"  want {json.dumps(want)}")
                print(f"  got  {json.dumps(got)}")
    passed = len(module.TEST_CASES) - len(failures)
    print(f"{passed}/{len(module.TEST_CASES)} passed, {len(critical_failures)} critical failures "
          f"(confidence gate {min_confidence})")
    return passed >= round(0.9 * len(module.TEST_CASES)) and not critical_failures
