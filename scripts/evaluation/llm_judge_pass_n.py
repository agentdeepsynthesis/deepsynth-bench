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
LLM-as-Judge Pass@N Evaluation for DeepSynth Benchmark.

Judges multiple candidate responses per question (Pass@N) using an LLM,
then computes aggregate metrics including pass rate and best precision.

Usage:
    python llm_judge_pass_n.py <results.json> [--reference REF.json] [--judge_model MODEL]
"""

import argparse
import json
import os
import re
import sys
import time

from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_JUDGE_MODEL = "gpt-4.1"
DEFAULT_REFERENCE = "DEEPSYNTH_lite.json"
OUTPUT_DIR = "llm_judge_score_pass_n"

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
within a margin of 1-5.5 percentage points for numerical problems. 'no' otherwise.

precision: '1' if extracted_final_answer matches [correct_answer]. '0' otherwise. \
For numeric [correct_answer], compute the normalised similarity score:
[1 - (abs(abs([correct_answer]) - abs(extracted_final_answer)) / \
max(abs([correct_answer]), abs(extracted_final_answer)))]

final precision: The precision score from above as a single number.

overlapping answers: All answers in [response] that also appear in \
[correct_answer] (equivalent or within 1-5.5 pp for numbers), delimited by \
'###'. Output 'NULL' if zero overlapping answers.
"""


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def ask_question(
    question: str,
    correct_answer: str,
    response: str,
    model: str = DEFAULT_JUDGE_MODEL,
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
# Pass@N Metrics
# ---------------------------------------------------------------------------

def compute_pass_at_n_metrics(judge_results: list[dict]) -> dict:
    """Compute Pass@N metrics from judge results grouped by question.

    Returns a dict with total questions, pass rate, and precision stats.
    """
    by_question: dict[str, list[dict]] = {}
    for entry in judge_results:
        by_question.setdefault(entry["id"], []).append(entry)

    total_questions = len(by_question)
    pass_count = 0
    all_precisions: list[float] = []
    best_precisions: list[float] = []

    for qid, entries in by_question.items():
        precisions: list[float] = []
        any_correct = False

        for entry in entries:
            raw_out = entry.get("out", "")
            try:
                out_dict = eval(raw_out) if isinstance(raw_out, str) else raw_out
            except Exception:
                out_dict = {}

            if str(out_dict.get("Correct", "no")).strip().lower() == "yes":
                any_correct = True

            try:
                prec = float(
                    out_dict.get("Final Precision", out_dict.get("Precision", 0))
                )
            except (ValueError, TypeError):
                prec = 0.0

            precisions.append(prec)
            all_precisions.append(prec)

        if any_correct:
            pass_count += 1
        if precisions:
            best_precisions.append(max(precisions))

    n_values = sorted({len(entries) for entries in by_question.values()})

    return {
        "total_questions": total_questions,
        "N_per_question": n_values,
        "pass_at_n": pass_count / total_questions if total_questions > 0 else 0,
        "pass_count": pass_count,
        "avg_precision_all": (
            sum(all_precisions) / len(all_precisions) if all_precisions else 0
        ),
        "avg_best_precision": (
            sum(best_precisions) / len(best_precisions) if best_precisions else 0
        ),
    }


def print_summary(metrics: dict) -> None:
    """Pretty-print the Pass@N summary to stdout."""
    print("\n" + "=" * 60)
    print("PASS@N SUMMARY")
    print("=" * 60)
    print(f"  Total questions      : {metrics['total_questions']}")
    print(f"  N per question       : {metrics['N_per_question']}")
    print(
        f"  Pass@N               : {metrics['pass_at_n']:.4f} "
        f"({metrics['pass_count']}/{metrics['total_questions']})"
    )
    print(f"  Avg precision (all)  : {metrics['avg_precision_all']:.4f}")
    print(f"  Avg best precision   : {metrics['avg_best_precision']:.4f}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge Pass@N evaluation for DeepSynth Benchmark."
    )
    parser.add_argument(
        "results_file",
        help="Path to generation results JSON (from generate_pass_n.py)",
    )
    parser.add_argument(
        "--reference",
        type=str,
        default=DEFAULT_REFERENCE,
        help="Reference benchmark file (default: %(default)s)",
    )
    parser.add_argument(
        "--judge_model",
        type=str,
        default=DEFAULT_JUDGE_MODEL,
        help="Judge model name (default: %(default)s)",
    )
    args = parser.parse_args()

    # Derive output paths
    model_name = (
        args.results_file.rstrip("/").split("/")[-2]
        if "/" in args.results_file
        else "unknown"
    )
    base_name = os.path.splitext(os.path.basename(args.results_file))[0]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"judge_{model_name}_{base_name}.json")
    summary_file = os.path.join(OUTPUT_DIR, f"summary_{model_name}_{base_name}.json")

    # Load inputs
    with open(args.results_file, "r") as fh:
        gen_results = json.load(fh)
    with open(args.reference, "r") as fh:
        bench = json.load(fh)

    ref_lookup = {q["Question Number"]: q for q in bench}

    # Resume from existing judge output
    if os.path.exists(output_file):
        with open(output_file, "r") as fh:
            try:
                outputs = json.load(fh)
            except json.JSONDecodeError:
                outputs = []
    else:
        outputs = []

    judged_keys = {
        (entry["id"], entry.get("pass_index", 0)) for entry in outputs
    }

    # Judge each response
    for entry in gen_results:
        question_id = entry["Question Number"]
        pass_idx = entry.get("pass_index", 0)
        response = entry["answer"]

        if (question_id, pass_idx) in judged_keys:
            print(f"Skipping Question {question_id}, pass {pass_idx} (already judged)")
            continue

        if question_id not in ref_lookup:
            print(f"Warning: Question {question_id} not in reference file, skipping")
            continue

        ref = ref_lookup[question_id]
        print(f"Judging Question {question_id}, pass {pass_idx}...")

        start_time = time.time()
        answer, full_context = ask_question(
            ref["Questions"], ref["Answers"], response, args.judge_model
        )
        execution_time = time.time() - start_time

        parsed = parse_judge_output(answer)
        print(f"  Result: {parsed}")
        print(f"  Time:   {execution_time:.2f}s")

        outputs.append(
            {
                "id": question_id,
                "pass_index": pass_idx,
                "answer": answer,
                "reasoning": str(full_context),
                "out": str(parsed),
                "time": execution_time,
            }
        )

        # Save incrementally
        with open(output_file, "w") as fh:
            json.dump(outputs, fh, indent=4)

    # Compute and save summary
    metrics = compute_pass_at_n_metrics(outputs)
    print_summary(metrics)

    with open(summary_file, "w") as fh:
        json.dump(metrics, fh, indent=4)
    print(f"\nSummary saved to {summary_file}")


if __name__ == "__main__":
    main()
