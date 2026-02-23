<div align="center">
<img src="images/octopus_logo.png" alt="DEEPSYNTH Bench" width="400"/>


# DEEPSYNTH: A Benchmark for Deep Information Synthesis

![Image](https://github.com/agentdeepsynthesis/deepsynth-bench/blob/main/images/deepsynth_figure1.gif)
</div>


## Repository Structure
```
deepsynth-benchmark/
├── README.md
├── DEEPSYNTH_lite.json          # Dev set: 40 tasks with questions, answers, and plans
├── decompositions/
│   ├── 003.json                 # Detailed decomposition with intermediate answers
│   └── intermediate_answers_schemas/
│       └── 003.schema.json      # JSON schema for intermediate answer types
├── evaluation/
│   ├── evaluate.py              # Evaluation script
│   └── metrics.py               # F1, EM, and LLM-judge metrics
└── assets/
    └── deepsynth_overview.png
```

```
1. *DEEPSYNTH_lite.json:* contains  (Dev set) 40 tasks (with questions, answers, and intermediate steps (plan))
2. *decompositions/intermediate_answers_schemas/003.schema.json:* one example from the dev set with the schema for the intermediate answer types.
3. *decompositions/003.json:* contains the decomposition and intermediate answers. 
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

# Load the dev set
with open('DEEPSYNTH_lite.json', 'r') as f:
    benchmark = json.load(f)

# Iterate over tasks
for task in benchmark['tasks']:
    question = task['question']
    expected_answer = task['answer']
    steps = task['intermediate_steps']
    
    # Your agent code here
    prediction = your_agent.solve(question)
    
    # Evaluate
    score = evaluate(prediction, expected_answer)
```

Disclaimer: This open source project is not an official Huawei product, Huawei is not expected to provide support for this project
