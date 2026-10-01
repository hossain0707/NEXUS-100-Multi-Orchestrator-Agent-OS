# NEXUS-100 Benchmark Suite

This suite measures what the current implementation can actually demonstrate today:
routing quality, routing latency, and approval-policy correctness.

It deliberately does **not** label NEXUS-100 as "better than ChatGPT." NEXUS-100 is currently an orchestration/control layer, while ChatGPT supplies general-purpose model reasoning in the ChatGPT integration.

## Automated benchmark

Run:

```bash
python benchmarks/run.py
```

Optionally write reproducible artifacts:

```bash
python benchmarks/run.py \
  --json benchmarks/results/latest.json \
  --markdown benchmarks/results/latest.md
```

The corpus in `benchmarks/cases.json` currently contains 20 routing cases and 8 governance cases spanning all 10 domains.

### Metrics

- **Routing precision** — how much of the selected route is relevant.
- **Routing recall** — how much of the expected route was recovered.
- **Routing macro F1** — balanced routing score across benchmark cases.
- **Exact-match rate** — percentage of prompts whose selected domain set exactly matches the expected set.
- **Router latency** — local deterministic routing time; this is not end-to-end ChatGPT latency.
- **Governance accuracy** — whether sensitive scopes/high-risk actions are correctly sent to human approval.

## NEXUS-100 vs ChatGPT A/B protocol

For a fair comparison, use the same task wording in two fresh chats/runs:

1. **ChatGPT-only baseline:** do not enable NEXUS-100. Ask ChatGPT to complete the task directly.
2. **ChatGPT + NEXUS-100:** enable NEXUS-100 and ask it to plan or run the same task.
3. Keep the model, task wording, and available external information the same.
4. Record latency and, where available, token/API usage.
5. Blind-score both outputs before revealing which system produced each answer.

Recommended human scoring rubric (1-5 each):

| Dimension | What to judge |
|---|---|
| Correctness | Factual and technical correctness |
| Completeness | Coverage of required subtasks |
| Decomposition | Quality of task breakdown |
| Routing | Whether appropriate domains/agents were selected |
| Tool use | Whether tools were selected and used appropriately |
| Cross-domain coordination | Quality of handoffs and synthesis |
| Safety/governance | Correct approval behavior for consequential actions |
| Reproducibility | Whether repeated runs remain structurally consistent |

Report answer-quality results only after the scored A/B runs exist. Do not infer an answer-quality advantage from the automated routing benchmark.

## Suggested benchmark task

```text
Design a production deployment plan for an 8B LLM on GPUs,
estimate infrastructure requirements and cost, identify security risks,
and produce an implementation roadmap.
```

ChatGPT-only prompt: use the task exactly as written.

NEXUS-100 prompt:

```text
Use NEXUS-100 to plan this mission:
Design a production deployment plan for an 8B LLM on GPUs,
estimate infrastructure requirements and cost, identify security risks,
and produce an implementation roadmap.
```

The expected advantage, if one exists, should appear in measurable orchestration behavior rather than being assumed from the number of registered agents.
