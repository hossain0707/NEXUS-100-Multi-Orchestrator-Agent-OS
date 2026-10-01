# NEXUS-100 benchmark result

Benchmark corpus: 20 routing cases + 8 governance cases.

| Metric | Result |
|---|---:|
| Routing macro precision | 0.926 |
| Routing macro recall | 0.938 |
| Routing macro F1 | 0.916 |
| Routing exact-match rate | 70.0% |
| Governance approval accuracy | 100.0% |

These results measure deterministic routing and approval-policy behavior only. They do not measure general reasoning quality and do not establish that NEXUS-100 is more intelligent than ChatGPT.

For answer-quality comparison, use the controlled ChatGPT-only vs ChatGPT + NEXUS-100 A/B protocol in `benchmarks/README.md`.
