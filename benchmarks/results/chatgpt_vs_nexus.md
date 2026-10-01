# ChatGPT vs NEXUS-100 comparative routing benchmark

Date: 2026-10-01

This comparison uses the same 20 routing prompts and the same gold domain labels from `benchmarks/cases.json`.

## Systems compared

- **ChatGPT-only baseline:** one GPT-5.6 Sol classification pass in ChatGPT, instructed to select only directly necessary domains from the same 10-domain taxonomy.
- **NEXUS-100:** the repository's deterministic Meta Orchestrator routing benchmark.

This is a **routing benchmark**, not a general intelligence or answer-quality benchmark. NEXUS-100 currently exposes planning/orchestration rather than a complete independent specialist-execution stack, so a full answer-quality comparison would not yet be apples-to-apples.

## Results

| System | Macro precision | Macro recall | Macro F1 | Exact-match rate |
|---|---:|---:|---:|---:|
| ChatGPT-only baseline | **1.000** | **0.975** | **0.983** | **95.0%** |
| NEXUS-100 router | 0.926 | 0.938 | 0.916 | 70.0% |

NEXUS-100 governance benchmark remains **100.0% approval accuracy** on the 8 governance cases.

## Interpretation

On this small fixed routing corpus, the ChatGPT-only baseline selected the gold domain set more accurately than the current keyword-based NEXUS-100 router. The main value NEXUS-100 demonstrates today is not superior raw routing intelligence; it is a structured orchestration layer with explicit domains, agent identities, mission tracking, policy boundaries, and MCP integration.

The comparison identifies a concrete engineering target: replace or augment keyword routing with model-backed or learned routing, then rerun the same corpus and report the new numbers.

## Baseline predictions

| Case | ChatGPT-only prediction |
|---|---|
| R01 | research |
| R02 | engineering |
| R03 | business |
| R04 | data |
| R05 | infrastructure, security |
| R06 | security |
| R07 | productivity |
| R08 | finance, infrastructure |
| R09 | career |
| R10 | personal |
| R11 | research, infrastructure, finance, security |
| R12 | engineering, data, infrastructure, security |
| R13 | data, business |
| R14 | research, infrastructure |
| R15 | engineering, security, infrastructure |
| R16 | productivity, business |
| R17 | finance, infrastructure |
| R18 | career, productivity |
| R19 | research, data |
| R20 | personal, finance |

The only exact-match miss in this baseline was R02, where the prompt asked to build/test a Python API but did not explicitly ask for a security review; the gold label also includes `security`.
