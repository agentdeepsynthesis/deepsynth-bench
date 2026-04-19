<p align="center">
  <img src="assets/octopus_logo.png" alt="DeepSynth" width="180"/>
</p>

<h1 align="center">DeepSynth: A Benchmark for Deep Information Synthesis</h1>

<p align="center">
  <a href="https://arxiv.org/abs/2602.21143"><img alt="Paper" src="https://img.shields.io/badge/paper-arXiv-b31b1b"></a>
  <a href="https://huggingface.co/datasets/DeepSynthesisTeam/deepsynth-bench"><img alt="Dataset" src="https://img.shields.io/badge/🤗-dataset-yellow"></a>
  <a href="https://huggingface.co/spaces/DeepSynthesisTeam/deepsynth-leaderboard"><img alt="Leaderboard" src="https://img.shields.io/badge/🤗-leaderboard-orange"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue"></a>
  <img alt="ICLR" src="https://img.shields.io/badge/ICLR-2026-6c5ce7">
</p>

<p align="center">
  <img src="assets/deepsynth_figure1.gif" alt="DeepSynth overview" width="720"/>
</p>

> **TL;DR** — DeepSynth is a benchmark of **120 expert-curated tasks across 7 domains and 67 countries** that evaluates LLM agents on multi-step web information synthesis. Unlike shallow retrieval benchmarks, DeepSynth tasks require combining evidence across many sources to produce a single structured answer.

---

## 📋 Table of Contents

- [Quickstart](#-quickstart)
- [Leaderboard](#-leaderboard)
- [Dataset](#-dataset)
- [Evaluation](#-evaluation)
- [Submitting to the Leaderboard](#-submitting-to-the-leaderboard)
- [Baselines](#-baselines)
- [Citation](#-citation)

---

## 🚀 Quickstart

```bash
# 1. Clone
git clone https://github.com/agentdeepsynthesis/deepsynth-bench
cd deepsynth-bench

# 2. Install
pip install -r requirements.txt

# 3. Download the dev set from Hugging Face (requires `huggingface-cli login` once)
python scripts/download_data.py --split dev

# 4. Evaluate a sample prediction file
python scripts/evaluation/eval_static_score.py \
    --predictions examples/sample_predictions.json \
    --split dev
```

Expected output:

```
EM: 0.175 | F1: 0.304 | LLM-Judge: 0.392
```

---

## 🏆 Leaderboard

Current top entries on the **test** split (120 tasks):

| Rank | Agent | Base Model | Scaffold | EM | F1 | LLM-Judge | Avg Cost |
|------|-------|------------|----------|----|----|-----------|----------|
| 1 | DeepSynth-Planner | claude-opus-4-6 | Plan-and-Execute | 0.27 | 0.42 | **0.53** | $0.61 |
| 2 | ReAct-Claude | claude-opus-4-6 | ReAct | 0.22 | 0.38 | 0.47 | $0.44 |
| 3 | ReAct-GPT4o | gpt-4o-2024-08-06 | ReAct | 0.18 | 0.31 | 0.41 | $0.38 |
| 4 | CodeAct-Gemini | gemini-2.5-pro | CodeAct | 0.17 | 0.30 | 0.39 | $0.29 |
| 5 | Vanilla-Llama | llama-3.3-70b | none | 0.08 | 0.19 | 0.22 | $0.04 |

> *Numbers above are illustrative placeholders — replace with Table 1 of the DeepSynth paper before publishing.*

👉 **[Full interactive leaderboard →](https://huggingface.co/spaces/DeepSynthesisTeam/deepsynth-leaderboard)**

---

## 📚 Dataset

DeepSynth is hosted on the Hugging Face Hub:
**[`DeepSynthesisTeam/deepsynth-bench`](https://huggingface.co/datasets/DeepSynthesisTeam/deepsynth-bench)**

| File | Size | Description |
|------|------|-------------|
| `DEEPSYNTH_lite.json` | 40 tasks | Dev set with questions, gold answers, and reasoning plans. Use for prototyping. |
| `deepsynth_questions_only_all.json` | 120 tasks | Test set — questions only. Submit predictions via the leaderboard. |
| `decompositions/*.json` | — | Intermediate-answer decompositions for selected tasks. |
| `intermediate_answers_schemas/*.json` | — | JSON Schemas defining intermediate-answer formats. |

```python
from huggingface_hub import hf_hub_download
import json

path = hf_hub_download(
    repo_id="DeepSynthesisTeam/deepsynth-bench",
    filename="DEEPSYNTH_lite.json",
    repo_type="dataset",
)
tasks = json.load(open(path))
```

---

## 📊 Evaluation

DeepSynth reports three complementary metrics:

| Metric | What it measures |
|--------|------------------|
| **Exact Match (EM)** | Strict: every key-value pair must match the gold answer. |
| **F1** | Partial credit across correct key-value pairs. |
| **LLM Judge** | Semantic equivalence with small numerical tolerance (1–5.5%). |

Run evaluation locally:

```bash
python scripts/evaluation/eval_static_score.py \
    --predictions your_predictions.json \
    --split test \
    --output results.json
```

The script prints aggregate scores and writes a per-task breakdown to `results.json`.

### Prediction format

```json
{
  "001": {"Sweden": 1.2, "Finland": 0.8},
  "002": {"Brunei": -0.67, "Singapore": -0.34}
}
```

For **leaderboard submissions**, wrap predictions in the full [submission schema](scripts/evaluation/submission_schema.json) — see below.

---

## 📤 Submitting to the Leaderboard

We use a **PR-based submission flow** for transparency and review.

### Step 1 — Produce a submission file

Wrap your predictions with required metadata. Full spec:
[`scripts/evaluation/submission_schema.json`](scripts/evaluation/submission_schema.json).

Minimal example:

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "agent_name": "MyAgent-v1",
    "base_model": "gpt-4o-2024-08-06",
    "scaffold": "ReAct",
    "tools_used": ["web_search", "python_interpreter"],
    "organization": "Your Org",
    "contact_email": "you@example.org",
    "code_url": "https://github.com/you/your-agent",
    "submission_date": "2026-04-18",
    "split": "test",
    "num_seeds": 3,
    "uses_external_retrieval": true
  },
  "predictions": {
    "001": {"answer": {"Sweden": 1.2, "Finland": 0.8}, "cost_usd": 0.42, "latency_s": 18.3},
    "002": {"answer": {"Brunei": -0.67}, "cost_usd": 0.31, "latency_s": 14.1}
  }
}
```

Per-task `cost_usd`, `latency_s`, `num_tool_calls`, and token counts are optional but strongly encouraged — the leaderboard surfaces efficiency rankings that help your method stand out.

### Step 2 — Validate locally

```bash
python scripts/evaluation/validate_submission.py my_submission.json --strict
```

### Step 3 — Open a PR

Fork this repo and add your file to `submissions/`:

```
submissions/2026-04-18-yourorg-agentname.json
```

CI runs schema validation and score computation automatically. Once a maintainer merges, your row appears on the [leaderboard](https://huggingface.co/spaces/DeepSynthesisTeam/deepsynth-leaderboard) within ~5 minutes.

### What we require

- A **public `code_url`** that reproduces your numbers. Submissions without reproducible code will not be accepted.
- Honest metadata. Misreporting scaffold or tool access is grounds for retraction.
- We reserve the right to ask for a run trace for spot-check verification.

### Retraction policy

Email the contact on the submission file. Corrections and retractions are logged transparently in the leaderboard history.

---

## 🧪 Baselines

Runnable baseline agents live in [`scripts/baselines/`](scripts/baselines/):

- `vanilla/` — LLM-only, no tools.
- `react/` — ReAct with web search and Python.
- `codeact/` — CodeAct style with full Python sandbox.
- `plan_and_execute/` — Two-stage planner + executor.

Each baseline has its own `README.md` with model setup, API key requirements, and an end-to-end run command.

---

## 📜 Citation

If you use DeepSynth in your research, please cite:

```bibtex
@inproceedings{deepsynth2026,
  title     = {DeepSynth: A Benchmark for Deep Information Synthesis},
  author    = {DeepSynth Team},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2026},
  url       = {https://arxiv.org/abs/2602.21143}
}
```

A [`CITATION.cff`](CITATION.cff) file is provided for GitHub's "Cite this repository" button.

---

## 📄 License

Apache License 2.0. See [LICENSE](LICENSE).

## 🙏 Acknowledgements

Developed across Huawei Noah's Ark Lab, Imperial College London, UCL, University of Zurich, University of Sheffield, and University of Cambridge.

> *Disclaimer: This open-source project is not an official Huawei product; Huawei is not expected to provide support.*
