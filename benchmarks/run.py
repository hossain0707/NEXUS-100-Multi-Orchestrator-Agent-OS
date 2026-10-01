from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from nexus.models import Risk
from nexus.orchestrator import orchestrator
from nexus.policy import policy


ROOT = Path(__file__).resolve().parent
DEFAULT_CASES = ROOT / "cases.json"


def _f1(expected: set[str], predicted: set[str]) -> tuple[float, float, float]:
    if not predicted:
        precision = 0.0
    else:
        precision = len(expected & predicted) / len(predicted)
    recall = len(expected & predicted) / len(expected) if expected else 1.0
    if precision + recall == 0:
        return precision, recall, 0.0
    return precision, recall, 2 * precision * recall / (precision + recall)


def run(cases_path: Path = DEFAULT_CASES) -> dict:
    corpus = json.loads(cases_path.read_text(encoding="utf-8"))

    routing = []
    latencies = []
    for case in corpus["routing_cases"]:
        started = time.perf_counter()
        route = orchestrator.route(case["prompt"])
        latency_ms = (time.perf_counter() - started) * 1000
        latencies.append(latency_ms)

        expected = set(case["expected_domains"])
        predicted = {step.domain for step in route}
        precision, recall, f1 = _f1(expected, predicted)
        routing.append(
            {
                "id": case["id"],
                "expected": sorted(expected),
                "predicted": sorted(predicted),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "exact_match": expected == predicted,
                "latency_ms": latency_ms,
            }
        )

    governance = []
    for case in corpus["governance_cases"]:
        decision = policy.evaluate(set(case["scopes"]), Risk(case["risk"]))
        governance.append(
            {
                "id": case["id"],
                "expected_requires_approval": case["requires_approval"],
                "actual_requires_approval": decision.requires_approval,
                "correct": decision.requires_approval == case["requires_approval"],
            }
        )

    return {
        "corpus_version": corpus["version"],
        "routing_cases": len(routing),
        "governance_cases": len(governance),
        "routing": {
            "macro_precision": statistics.fmean(item["precision"] for item in routing),
            "macro_recall": statistics.fmean(item["recall"] for item in routing),
            "macro_f1": statistics.fmean(item["f1"] for item in routing),
            "exact_match_rate": statistics.fmean(
                1.0 if item["exact_match"] else 0.0 for item in routing
            ),
            "latency_ms_median": statistics.median(latencies),
            "latency_ms_max": max(latencies),
        },
        "governance": {
            "accuracy": statistics.fmean(
                1.0 if item["correct"] else 0.0 for item in governance
            )
        },
        "details": {
            "routing": routing,
            "governance": governance,
        },
    }


def markdown(result: dict) -> str:
    r = result["routing"]
    g = result["governance"]
    return "\n".join(
        [
            "# NEXUS-100 benchmark result",
            "",
            f"- Routing cases: {result['routing_cases']}",
            f"- Governance cases: {result['governance_cases']}",
            f"- Routing macro precision: {r['macro_precision']:.3f}",
            f"- Routing macro recall: {r['macro_recall']:.3f}",
            f"- Routing macro F1: {r['macro_f1']:.3f}",
            f"- Routing exact-match rate: {r['exact_match_rate']:.3f}",
            f"- Median router latency: {r['latency_ms_median']:.3f} ms",
            f"- Governance accuracy: {g['accuracy']:.3f}",
            "",
            "These numbers measure routing and approval-policy behavior only.",
            "They do not claim that NEXUS-100 is more intelligent than ChatGPT.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NEXUS-100 deterministic benchmark")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    result = run(args.cases)
    print(json.dumps(result, indent=2))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(result) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
