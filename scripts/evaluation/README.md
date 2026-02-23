# Evaluation Scripts

This directory contains the evaluation pipeline for the **DeepSynth Benchmark**. There are two complementary evaluation approaches — a deterministic static scorer and an LLM-as-Judge scorer — that together provide a robust picture of model performance.

## Overview

| Script | Method | Metrics |
|---|---|---|
| `eval_static_score.py` | Deterministic JSON comparison | Exact match accuracy, partial similarity, precision, recall, F1 |
| `llm_judge.py` | LLM-as-Judge (single pass) | Per-question correctness, precision, overlapping answers |
| `llm_judge_pass_n.py` | LLM-as-Judge (Pass@N) | Pass@N rate, average precision, best-of-N precision |

## Prerequisites

- **Python 3.10+**
- **OpenAI Python SDK** — required by the LLM judge scripts:
  ```bash
  pip install openai
  ```
- **`OPENAI_API_KEY`** environment variable set for LLM judge scripts.
- **Reference benchmark files** in the working directory:
  - `DEEPSYNTH_lite.json` — development set (used by `llm_judge.py` and `llm_judge_pass_n.py`)
  - `deep_insight_bench_v5_90.json` — test set (used by `eval_static_score.py`)

## Scripts

### 1. `eval_static_score.py` — Static F1 Evaluation

Performs a fully deterministic, offline comparison between gold-standard JSON answers and model-generated JSON outputs. No API calls are required.

**What it does:**

- Parses and normalises both gold and model JSON (handles markdown fences, `<Answer>:` prefixes, single quotes, etc.)
- Flattens nested JSON into dot-notation keys for granular comparison
- Computes exact match accuracy, partial similarity (numeric tolerance + character Jaccard), precision, recall, and F1

**Usage:**

```bash
python scripts/evaluation/eval_static_score.py <model_output.json>
```

The model output file should be a JSON array where each entry has `"Question Number"` and `"answer"` fields.

**Example output:**

```
Evaluation Results
==================
Partial Exact Match Accuracy : 72.50%
Strict Exact Match Accuracy  : 65.00%
Partial Score (Similarity)   : 78.34%
Precision                    : 74.12%
Recall                       : 71.88%
F1 Score                     : 72.98%
```

---

### 2. `llm_judge.py` — LLM-as-Judge (Single Pass)

Uses an LLM (default: `gpt-4.1`) to semantically judge each model response against the gold answer. This captures correctness that a rigid string comparison might miss.

**What it does:**

- Sends each (question, response, correct_answer) triple to the judge model
- The judge extracts the final answer, determines correctness, and computes a precision score
- Results are saved incrementally so interrupted runs can be resumed

**Usage:**

```bash
python scripts/evaluation/llm_judge.py <model_name/results.json>
```

The model name is inferred from the parent directory of the input file. Results are saved to `llm_judge_score_dev/owl_<model_name>.json`.

---

### 3. `llm_judge_pass_n.py` — LLM-as-Judge with Pass@N

Extends the LLM judge to evaluate multiple candidate responses per question (Pass@N). A question is considered "passed" if **any** of its N candidates is judged correct.

**What it does:**

- Judges each (question, pass_index) pair independently
- Supports resumption — already-judged pairs are skipped automatically
- Computes Pass@N rate, average precision across all candidates, and average best-of-N precision

**Usage:**

```bash
python scripts/evaluation/llm_judge_pass_n.py <results.json> \
    --reference DEEPSYNTH_lite.json \
    --judge_model gpt-4.1
```

| Argument | Default | Description |
|---|---|---|
| `results_file` | *(required)* | Path to generation results JSON |
| `--reference` | `DEEPSYNTH_lite.json` | Reference benchmark file |
| `--judge_model` | `gpt-4.1` | Model used as the judge |

**Example output:**

```
============================================================
PASS@N SUMMARY
============================================================
  Total questions      : 80
  N per question       : [3]
  Pass@N               : 0.8125 (65/80)
  Avg precision (all)  : 0.7234
  Avg best precision   : 0.8542
============================================================
```

## Input Format

All scripts expect model output as a JSON array:

```json
[
  {
    "Question Number": 1,
    "answer": "The answer text or JSON ...",
    "pass_index": 0
  }
]
```

- `"Question Number"` — must match the reference benchmark IDs.
- `"answer"` — the model's response (may contain `<Answer>:` prefixes, markdown, etc.).
- `"pass_index"` — *(Pass@N only)* zero-based index of the candidate.

## Output Structure

```
llm_judge_score_dev/
  owl_<model_name>.json           # Per-question judge results (single pass)

llm_judge_score_pass_n/
  judge_<model>_<file>.json       # Per-question judge results (Pass@N)
  summary_<model>_<file>.json     # Aggregate Pass@N metrics
```
