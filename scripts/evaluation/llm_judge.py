# Copyright (C) 2026. Huawei Technologies Co., Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================


"""
LLM-as-Judge Evaluation for DeepSynth Benchmark.

Uses an LLM (e.g. GPT-4.1) to judge whether model-generated responses
match the gold-standard correct answers, outputting per-question precision
scores and reasoning.

Usage:
    python llm_judge.py <model_output_dir/results.json>
"""

import json
import os
import re
import sys
import time

from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JUDGE_MODEL = "gpt-4.1"
REFERENCE_FILE = "DEEPSYNTH_lite.json"
OUTPUT_DIR = "llm_judge_score_dev"

client = OpenAI(timeout=3600)


# ---------------------------------------------------------------------------
# Judge Prompt
# ---------------------------------------------------------------------------

JUDGE_PROMPT_TEMPLATE = """\
Judge whether the following [response] to [question] is correct or not \
based on the precise and unambiguous [correct_answer] below.

[question]: {question}
[response]: {response}
[correct_answer]: {correct_answer}

Your judgment must follow the format and criteria below:

extracted_final_answer: The final exact answer extracted from the [response]. \
Put the extracted answer as 'None' if there is no exact final answer to extract.

[correct_answer]: {correct_answer}

final answer length: The overall number of unique answers that appear in \
[response], not just correct ones. Provide a number, not an estimate.

reasoning: Explain why the extracted_final_answer is correct or incorrect \
based on [correct_answer]. Focus only on meaningful differences. Do not \
comment on background, attempt to solve the problem, or argue for any answer \
different than [correct_answer].

correct: 'yes' if extracted_final_answer matches [correct_answer], or is \
within a margin of 1–5.5 percentage points for numerical problems. 'no' otherwise.

precision: '1' if extracted_final_answer matches [correct_answer]. '0' otherwise. \
For numeric [correct_answer], compute the normalised similarity score:
[1 - (abs(abs([correct_answer]) - abs(extracted_final_answer)) / \
max(abs([correct_answer]), abs(extracted_final_answer)))]

final precision: The precision score from above as a single number.

overlapping answers: All answers in [response] that also appear in \
[correct_answer] (equivalent or within 1–5.5 pp for numbers), delimited by \
'###'. Output 'NULL' if zero overlapping answers.
"""


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def ask_question(
    question: str,
    correct_answer: str,
    response: str,
    model: str = JUDGE_MODEL,
) -> tuple[str, object]:
    """Send a judging request to the LLM and return (output_text, raw_result)."""
    judge_instructions = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        response=response,
        correct_answer=correct_answer,
    )

    result = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": judge_instructions},
            {
                "role": "user",
                "content": (
                    f"[question]: {question}\n"
                    f"[response]: {response}\n"
                    f"[correct_answer]: {correct_answer}"
                ),
            },
        ],
    )
    return result.output_text, result


def parse_judge_output(answer: str) -> dict[str, str]:
    """Extract key-value pairs from the judge's free-text output."""
    pattern = r"(\w[\w\s]*):\s*(\w+|NULL|\d+(\.\d+)?)"
    matches = re.findall(pattern, answer, re.IGNORECASE)
    return {key.strip().title(): value for key, value, _ in matches}


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python llm_judge.py <model_output.json>")
        sys.exit(1)

    file_path = sys.argv[1]
    model_name = file_path.split("/")[-2]
    print(f"Model: {model_name}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"owl_{model_name}.json")

    # Load model results
    if os.path.exists(file_path):
        with open(file_path, "r") as fh:
            results = json.load(fh)
    else:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Load reference benchmark
    with open(REFERENCE_FILE, "r") as fh:
        bench = json.load(fh)

    outputs: list[dict] = []
    all_output_scores: list[dict] = []

    for idx, question in enumerate(bench, start=1):
        user_question = question["Questions"]
        question_id = question["Question Number"]
        print(f"Processing Question {idx}: {user_question}")

        # Find matching response
        response = ""
        for entry in results:
            if question_id == entry["Question Number"]:
                response = entry["answer"]
                break
        if not response:
            print(f"  No response found for Question {question_id}, stopping.")
            break

        start_time = time.time()
        answer, full_context = ask_question(
            user_question, question["Answers"], response
        )
        execution_time = time.time() - start_time

        parsed = parse_judge_output(answer)
        print(f"  Result: {parsed}")
        print(f"  Time:   {execution_time:.2f}s\n")

        all_output_scores.append(parsed)
        outputs.append(
            {
                "id": question_id,
                "answer": answer,
                "reasoning": str(full_context),
                "out": str(parsed),
                "time": execution_time,
            }
        )

        # Save incrementally
        with open(output_file, "w") as fh:
            json.dump(outputs, fh, indent=4)

    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
