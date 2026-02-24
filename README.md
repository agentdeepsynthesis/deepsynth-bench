<div align="center">
<img src="assets/octopus_logo.png" alt="DEEPSYNTH Bench" width="400"/>


# A Benchmark for Deep Information Synthesis

![Image](https://github.com/agentdeepsynthesis/deepsynth-bench/blob/main/assets/deepsynth_figure1.gif)
</div>

## Repository Structure
```
deepsynth-benchmark/
├── README.md
├── data/
│   ├──DEEPSYNTH_lite.json          # Dev set: 40 tasks with questions, answers, and plans
├── evaluation/
│   ├── evaluate.py                # Evaluation script
│   └── metrics.py                 # F1, EM, and LLM-judge metrics
└── assets/
    └── deepsynth_overview.png
```

## Evaluation

### Metrics

We provide three evaluation metrics:

| Metric | Description |
|--------|-------------|
| **Exact Match (EM)** | All keys and values must be exactly correct |
| **F1 Score** | Partial credit for correct key-value pairs |
| **LLM Judge** | Soft evaluation allowing semantic equivalence and small numerical margins (1-5.5%) |

### Running Evaluation

```bash
pip install -r requirements.txt

# Evaluate model predictions
python evaluation/evaluate.py \
  --predictions predictions.json \
  --ground_truth DEEPSYNTH_lite.json \
  --metrics f1,em,llm_judge
```

### Prediction Format

Model predictions should be a JSON file with task IDs mapped to answers:

```json
{
  "001": {"Sweden": 1.2, "Finland": 0.8},
  "002": {"Brunei": -0.67, "Singapore": -0.34},
  ...
}
```



## Quick Start

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

# Iterate over tasks
for task in benchmark['tasks']:
    question = task['question']
    expected_answer = task['answer']
    steps = task['intermediate_steps']
    
    # Your agent code here
    prediction = your_agent.solve(question)
    
```
### 📊 Evaluation 
```bash
python scripts/evaluation/eval_static_score.py model_output.json
```

### License
We follow Apache License Version 2.0. Please see the [License](LICENSE) file for more information.

Disclaimer: This open source project is not an official Huawei product, Huawei is not expected to provide support for this project.
