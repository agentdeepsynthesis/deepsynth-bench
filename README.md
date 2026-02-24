<div align="center">
<img src="assets/octopus_logo.png" alt="DEEPSYNTH Bench" width="400"/>


# A Benchmark for Deep Information Synthesis

![Image](https://github.com/agentdeepsynthesis/deepsynth-bench/blob/main/assets/deepsynth_figure1.gif)
</div>

**DEEPSYNTH-Bench** is a challenging benchmark designed to evaluate the ability of AI systems to perform *deep information synthesis* — integrating, reasoning over, and consolidating information from multiple sources to answer complex, multi-step questions. Unlike retrieval-focused benchmarks, DEEPSYNTH-Bench requires models to go beyond surface-level extraction and produce structured, precise answers that reflect genuine analytical reasoning.

Key properties of the benchmark:
- **Multi-step reasoning**: Questions require chaining several reasoning steps or data sources.
- **Structured outputs**: Answers are JSON dictionaries with specific keys and numeric/string values.
- **Rigorous evaluation**: Three complementary metrics assess both exact correctness and semantic equivalence.
- **Dev + Test split**: 40 public dev tasks with gold answers, full decompositions, and intermediate steps for rapid iteration; 80 held-out test tasks (questions only) for clean leaderboard evaluation — 120 tasks in total.


## Repository Structure

```
deepsynth-bench/
├── README.md
├── scripts/
│   ├── evaluation/
│   │   ├── eval_static_score.py      # EM and F1 evaluation
│   │   ├── llm_judge.py              # LLM-as-judge evaluation (single prediction)
│   │   └── llm_judge_pass_n.py       # LLM-as-judge for pass@n evaluation
│   └── baselines/                    # Baseline agent scripts
└── assets/
    └── deepsynth_figure1.gif
```

The benchmark data (questions, answers, decompositions) lives on [Hugging Face](https://huggingface.co/datasets/DeepSynthesisTeam/deepsynth-bench). See the [Dataset section](#-dataset) below.

---

## 🗂 Dataset

The dataset is hosted on Hugging Face at [`DeepSynthesisTeam/deepsynth-bench`](https://huggingface.co/datasets/DeepSynthesisTeam/deepsynth-bench).

| File | Split | Description |
|------|-------|-------------|
| `DEEPSYNTH_lite.json` | Dev (40 tasks) | Questions, gold answers, reasoning plans, and full decompositions with intermediate steps |
| `deepsynth_questions_only_all.json` | Test (80 tasks) | Questions only — for leaderboard submission |

### Loading the Data

```python
import json
from huggingface_hub import hf_hub_download

# Load the dev set (with gold answers)
dev_path = hf_hub_download(
    repo_id="DeepSynthesisTeam/deepsynth-bench",
    filename="DEEPSYNTH_lite.json",
    repo_type="dataset"
)
with open(dev_path, "r") as f:
    dev_set = json.load(f)

# Load the test set (questions only)
test_path = hf_hub_download(
    repo_id="DeepSynthesisTeam/deepsynth-bench",
    filename="deepsynth_questions_only_all.json",
    repo_type="dataset"
)
with open(test_path, "r") as f:
    test_set = json.load(f)
```

---

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/agentdeepsynthesis/deepsynth-bench.git
cd deepsynth-bench
pip install huggingface_hub
```

### 2. Run Evaluation on the Dev Set

Generate predictions for `DEEPSYNTH_lite.json` using your model, then run:

```bash
python scripts/evaluation/eval_static_score.py your_predictions.json
```

---

## 📊 Evaluation

### Prediction Format

Predictions should be a JSON file mapping task IDs to answer dictionaries:

```json
{
  "001": {"Sweden": 1.2, "Finland": 0.8},
  "002": {"Brunei": -0.67, "Singapore": -0.34}
}
```

Each key is a task ID (matching the benchmark), and each value is a dictionary of answer key-value pairs.

### Metrics

We provide three complementary evaluation metrics:

| Metric | Script | Description |
|--------|--------|-------------|
| **Exact Match (EM)** | `eval_static_score.py` | All keys and values must match exactly |
| **F1 Score** | `eval_static_score.py` | Partial credit for correct key-value pairs |
| **LLM Judge** | `llm_judge.py` | Semantic equivalence; allows small numerical margins (1–5.5%) |

#### Static Metrics (EM + F1)

```bash
python scripts/evaluation/eval_static_score.py your_predictions.json
```

#### LLM Judge

```bash
python scripts/evaluation/llm_judge.py your_predictions.json
```

#### LLM Judge — Pass@N

```bash
python scripts/evaluation/llm_judge_pass_n.py your_predictions_pass_n.json
```

### Decompositions & Validation Schemas

For questions in the dev set, the `decompositions/` directory (on HuggingFace) provides step-by-step breakdowns of the reasoning required to answer each question. Matching JSON schemas in `intermediate_answers_schemas/` define the expected format for intermediate answers, enabling structured validation of reasoning chains.

---

## Citation

If you use DEEPSYNTH-Bench in your research, please cite:

```bibtex
@inproceedings{paul-etal-2026-deepinfosynth,
  title = {A Benchmark for Deep Information Synthesis},
  author = {Paul, Debjit and Murphy, Daniel and Gritta, Milan and Cardenas, Ronald and Prokhorov, Victor and Bolliger, Lena Sophia and Toker, Aysim and Miles, Roy and Oncescu, Andreea-Maria and Sivakumar, Jasivan Alex and Borchert, Philipp and Elezi, Ismail and Zhang, Meiru and Lee, Ka Yiu and Zhang, Guchun and Wang, Jun and Lampouras, Gerasimos},
  booktitle = {The Fourteenth International Conference on Learning Representations},
  month = apr,
  year = {2026},
}
```


### License
We follow Apache License Version 2.0. Please see the [License](LICENSE) file for more information.

Disclaimer: This open source project is not an official Huawei product, Huawei is not expected to provide support for this project.
