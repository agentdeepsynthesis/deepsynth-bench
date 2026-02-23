---
license: cc-by-4.0
task_categories:
  - question-answering
  - text-generation
language:
  - en
tags:
  - benchmark
  - agents
  - information-synthesis
  - deep-research
  - multi-step-reasoning
  - web-browsing
  - tool-use
pretty_name: "DEEPSYNTH Bench"
size_categories:
  - n<1K
---

# 🐙 DEEPSYNTH: A Benchmark for Deep Information Synthesis

<p align="center">
  <img src="assets/octopus_logo.png" width="180" />
</p>

<p align="center">
  <strong>Published at ICLR 2026</strong> &nbsp;|&nbsp;
  <a href="https://openreview.net/pdf?id=0Dhpt9aY3n">📄 Paper</a> &nbsp;|&nbsp;
  <a href="#">💻 Code</a> &nbsp;|&nbsp;
  <a href="#">🌐 Project Page</a>
</p>

---

## 📌 Key Highlights

- **120 challenging tasks** requiring multi-step web browsing, data extraction, and structured reasoning
- **67 countries** and **7 domains** — the most geographically diverse agent benchmark to date
- **Non-memorizable answers** — gold-standard answers are intentionally non-retrievable via direct search
- **Multi-part JSON outputs** — each answer is a structured JSON object with multiple key-value pairs
- **Avg. 7.54 intermediate steps** and **4.2 web pages** per task, with ~5.5 hours of expert annotation time per task
- **Best model F1: 8.97** (o3-deep-research) — even SOTA agents solve only 3/120 tasks exactly
- **16 expert annotators** (81.25% PhD holders) with double-annotation validation

---

## ⚙️ Loading the Dataset

```python
from datasets import load_dataset

ds = load_dataset("DeepSynthesisTeam/deepsynth-bench")
```

---

## 📊 Dataset Structure

Each example in the dataset contains the following fields:

| Field | Type | Description |
|---|---|---|
| `unique_id` | `string` | Unique task identifier (e.g., `item-001`) |
| `question` | `string` | The full task question (avg. 78.49 tokens) |
| `answer` | `string` | Gold-standard answer as a JSON object or list of JSON objects |
| `reasoning_path` | `string` | Step-by-step reasoning chain with intermediate steps, tools, and code used |
| `urls` | `list[string]` | URLs of the data sources required to solve the task |
| `domain` | `string` | One of 7 domains: `socio-economic`, `finance`, `environment`, `science`, `education`, `transportation`, `political/socio-political` |
| `region` | `list[string]` | Geographic regions the task covers (e.g., `["Europe", "Asia"]`) |
| `synthesis_operations` | `list[string]` | Required operations: `trend_detection`, `average`, `correlation`, `ranking`, `anomaly_detection`, `counting_and_comparing`, `filtering` |
| `num_intermediate_steps` | `int` | Number of intermediate reasoning steps |
| `num_web_pages` | `int` | Number of web pages an agent needs to navigate |

### Example

```json
{
  "unique_id": "item-042",
  "question": "According to ASEAN stats, between 2016-2023, which ASEAN countries' exports in telecommunication, computer and information services had a negative correlation with the total nominal GDP of all ASEAN countries combined? The final answer should be presented as a JSON: keys should be these ASEAN countries, and values should be the pearson correlation value(s) rounded to two decimals.",
  "answer": "{\"Country_A\": -0.45, \"Country_B\": -0.32}",
  "reasoning_path": "1) Search for ASEAN trade statistics ... 2) Navigate to ... 3) Extract data ... 4) Compute Pearson correlation ...",
  "urls": ["https://data.aseanstats.org/..."],
  "domain": "finance",
  "region": ["Asia"],
  "synthesis_operations": ["correlation", "counting_and_comparing"],
  "num_intermediate_steps": 8,
  "num_web_pages": 3
}
```

---

## 📁 Directory Layout

```
deepsynth-bench/
├── README.md                  # This dataset card
├── data/
│   ├── deepsynth_test.jsonl   # Full test set (120 tasks)
│   └── deepsynth_dev.jsonl    # Dev/Lite split for prototyping
├── evaluation/
│   ├── evaluate.py            # Evaluation script (F1, EM, LLM-Judge)
│   └── llm_judge_prompt.txt   # Prompt used for LLM-as-a-judge metric
├── assets/
│   └── octopus_logo.png       # Project logo
└── LICENSE                    # CC-BY-4.0
```

---

## 🏷️ Dataset Splits

| Split | # Tasks | Purpose |
|---|---|---|
| **Test** | 120 | Full benchmark for final evaluation and leaderboard |
| **Dev (Lite)** | ~40 | Lightweight subset for rapid iteration and debugging |

---

## 📈 Benchmark Results (Pass@1)

| Model | F1 | EM | LLM Judge |
|---|---|---|---|
| o4-mini | 3.05 | 0.0 | 0.0 |
| GPT-4.1 | 3.46 | 0.0 | 0.0 |
| GPT-5.1 | 3.83 | 0.0 | 0.0 |
| Gemini-Pro-2.5 | 6.25 | 0.0 | 5.0 |
| GPT-5.2-Pro | 8.70 | 6.25 | 3.3 |
| DeepSeek-R1-Chat | 3.23 | 1.67 | 2.5 |
| **o3-deep-research** | **8.97** | **2.50** | **17.5** |
| Smolagent (GPT-5) | 6.42 | 1.67 | 2.5 |
| OWL (GPT-4.1) | 5.41 | 1.67 | 12.5 |

---

## 🔍 Synthesis Operations

| Operation | % of Tasks | Description |
|---|---|---|
| Counting & Comparing | 33.7% | Quantifying occurrences and comparing values across sources |
| Trend Detection | 20.9% | Identifying patterns or changes over time |
| Ranking | 19.8% | Ordering items based on specific criteria |
| Average | 11.1% | Summarising numerical data from multiple sources |
| Correlation | 7.0% | Measuring relationships between variables |
| Anomaly Detection | 7.0% | Identifying data points that deviate from the norm |
| Filtering | 0.6% | Selecting information based on criteria or thresholds |

---

## 📜 Citation

```bibtex
@inproceedings{paul2026deepsynth,
  title     = {{DEEPSYNTH}: A Benchmark for Deep Information Synthesis},
  author    = {Debjit Paul and Daniel Murphy and Milan Gritta and
               Ronald Cardenas and Victor Prokhorov and Lena Sophia Bolliger and
               Aysim Toker and Roy Miles and Andreea-Maria Oncescu and
               Jasivan Alex Sivakumar and Philipp Borchert and
               Ismail Elezi and Meiru Zhang and Ka Yiu Lee and
               Guchun Zhang and Jun Wang and
               Gerasimos Lampouras},
  booktitle = {The Fourteenth International Conference on
               Learning Representations (ICLR)},
  year      = {2026},
  url       = {https://openreview.net/forum?id=0Dhpt9aY3n}
}
```

---

## 📬 Contact

For questions, issues, or evaluation requests, please open an issue on GitHub or contact the authors.