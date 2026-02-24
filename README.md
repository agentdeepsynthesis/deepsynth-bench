<div align="center">
<img src="assets/octopus_logo.png" alt="DEEPSYNTH Bench" width="400"/>


# A Benchmark for Deep Information Synthesis

![Image](https://github.com/agentdeepsynthesis/deepsynth-bench/blob/main/assets/deepsynth_figure1.gif)
</div>

## Repository Structure
```
deepsynth-benchmark/
├── README.md
├── scripts/
│   ├── evaluation/
│   │   ├── eval_static_score.py
│   │   ├── llm_judge.py
│   │   ├── llm_judge_pass_n.py
│   └── baselines/
└── assets/
    └── deepsynth_overview.png
```


## 🗂 Dataset Files

| File                                | Description                                                            |
| ----------------------------------- | ---------------------------------------------------------------------- |
| `DEEPSYNTH_lite.json`               | Development set: 40 tasks with questions, answers, and reasoning plans |
| `deepsynth_questions_only_all.json` | Test set: questions only                                               |

```python
import json
from huggingface_hub import hf_hub_download
# Load the dev set
dev_path = hf_hub_download(
    repo_id="DeepSynthesisTeam/deepsynth-bench",
    filename="DEEPSYNTH_lite.json",
    repo_type="dataset"
)

with open('DEEPSYNTH_lite.json', 'r') as f:
    benchmark = json.load(f)
```

## Evaluation

### Metrics

We provide three evaluation metrics:

| Metric | Description |
|--------|-------------|
| **Exact Match (EM)** | All keys and values must be exactly correct |
| **F1 Score** | Partial credit for correct key-value pairs |
| **LLM Judge** | Soft evaluation allowing semantic equivalence and small numerical margins (1-5.5%) |


### Prediction Format

Model predictions should be a JSON file with task IDs mapped to answers:

```json
{
  "001": {"Sweden": 1.2, "Finland": 0.8},
  "002": {"Brunei": -0.67, "Singapore": -0.34},
  ...
}
```

### 📊 Evaluation 
```bash
python scripts/evaluation/eval_static_score.py model_output.json
```

### License
We follow Apache License Version 2.0. Please see the [License](LICENSE) file for more information.

Disclaimer: This open source project is not an official Huawei product, Huawei is not expected to provide support for this project.
