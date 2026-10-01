import json
from pathlib import Path

from benchmarks.run import run


def test_benchmark_corpus_and_runner():
    cases = Path("benchmarks/cases.json")
    corpus = json.loads(cases.read_text(encoding="utf-8"))

    assert len(corpus["routing_cases"]) == 20
    assert len(corpus["governance_cases"]) == 8

    result = run(cases)
    assert result["routing_cases"] == 20
    assert result["governance_cases"] == 8
    assert 0.0 <= result["routing"]["macro_f1"] <= 1.0
    assert 0.0 <= result["routing"]["exact_match_rate"] <= 1.0
    assert result["routing"]["latency_ms_median"] >= 0.0
    assert result["governance"]["accuracy"] == 1.0
