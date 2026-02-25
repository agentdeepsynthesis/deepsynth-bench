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
Static F1 Score Evaluation for DeepSynth Benchmark.

Computes exact match accuracy, partial similarity scores, precision, recall,
and F1 between gold-standard JSON answers and model-generated JSON outputs.

Usage:
    python eval_static_score.py <model_output.json>
"""

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Benchmark reference files (update paths as needed)
REFERENCE_FILE_TEST = "deepsynth_questions_only_all.json"
REFERENCE_FILE_DEV = "DEEPSYNTH_lite.json"

# Total number of questions used to normalise strict accuracy
TOTAL_QUESTIONS = 80


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class EvaluationResult:
    """Container for evaluation results with multiple scoring metrics."""

    exact_accuracy: float
    final_exact_accuracy: float
    partial_score: float
    precision: float
    recall: float
    f1_score: float
    total_gold_keys: int
    total_model_keys: int
    matched_keys: int       # Keys present in both gold and model
    exact_matches: int       # Keys with exactly matching values
    detailed_results: List[Tuple[str, str, str, bool, str]] = field(
        default_factory=list,
    )

    def __str__(self) -> str:
        missing_keys = self.total_gold_keys - self.matched_keys
        extra_keys = self.total_model_keys - self.matched_keys
        return (
            "\n"
            "Evaluation Results\n"
            "==================\n"
            f"Partial Exact Match Accuracy : {self.exact_accuracy:.2%}\n"
            f"Strict Exact Match Accuracy  : {self.final_exact_accuracy / TOTAL_QUESTIONS:.2%}\n"
            f"Partial Score (Similarity)   : {self.partial_score:.2%}\n"
            f"Precision                    : {self.precision:.2%}\n"
            f"Recall                       : {self.recall:.2%}\n"
            f"F1 Score                     : {self.f1_score:.2%}\n"
            "\n"
            "Key Statistics\n"
            "--------------\n"
            f"  Gold keys                  : {self.total_gold_keys}\n"
            f"  Model keys                 : {self.total_model_keys}\n"
            f"  Matched keys (both)        : {self.matched_keys}\n"
            f"  Exact value matches        : {self.exact_matches}\n"
            f"  Missing keys (in gold)     : {missing_keys}\n"
            f"  Extra keys (in model)      : {extra_keys}\n"
        )


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def extract_answer_from_text(text: str) -> str:
    """Extract the final answer from model output text.

    Looks for an ``<Answer>:`` token and returns everything after it.
    Falls back to the original text when the token is absent.
    """
    if not isinstance(text, str):
        return str(text)

    match = re.search(r"<Answer>\s*:?\s*(.*)$", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.strip()


def preprocess_model_output(
    model_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract concise answers from raw model output entries."""
    processed: List[Dict[str, Any]] = []
    for item in model_data:
        if "Question Number" not in item or "answer" not in item:
            print(f"Warning: Item missing 'Question Number' or 'answer' key: {item}")
            continue
        processed_item = item.copy()
        processed_item["answer"] = extract_answer_from_text(item["answer"])
        processed.append(processed_item)
    return processed


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_dataset_files(
    gold_file: str,
    model_file: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load and align gold and model datasets by Question Number.

    Returns:
        Tuple of ``(matched_gold_dict, matched_model_dict)`` keyed by ID.
    """
    with open(gold_file, "r", encoding="utf-8") as fh:
        gold_data = json.load(fh)
    with open(model_file, "r", encoding="utf-8") as fh:
        model_data = json.load(fh)

    model_data = preprocess_model_output(model_data)

    gold_dict = {
        str(item["Question Number"]): item
        for item in gold_data
        if "Question Number" in item
    }
    model_dict = {
        str(item["Question Number"]): item
        for item in model_data
        if "Question Number" in item
    }

    gold_ids = set(gold_dict.keys())
    model_ids = set(model_dict.keys())
    common_ids = gold_ids & model_ids

    print(f"Gold file contains  {len(gold_ids)} items")
    print(f"Model file contains {len(model_ids)} items")
    print(f"Common IDs          {len(common_ids)}")

    if gold_ids - model_ids:
        print(f"Warning: {len(gold_ids - model_ids)} IDs in gold but not in model")
    if model_ids - gold_ids:
        print(f"Warning: {len(model_ids - gold_ids)} IDs in model but not in gold")

    matched_gold = {id_: gold_dict[id_] for id_ in common_ids}
    matched_model = {id_: model_dict[id_] for id_ in common_ids}
    return matched_gold, matched_model


# ---------------------------------------------------------------------------
# JSON Parsing Helpers
# ---------------------------------------------------------------------------

def parse_json_string(content: str) -> Union[Dict, List]:
    """Parse a string that may contain JSON data.

    Handles standard JSON, Python literals, markdown code blocks,
    and various answer-prefix patterns.
    """
    if not isinstance(content, str):
        return content

    original_content = content
    content = content.strip()

    # Step 1: Strip markdown fences and common answer prefixes
    strip_patterns = [
        r"```json\s*",
        r"\s*```",
        r".*?<[Aa]nswer>\s*:?\s*",
        r".*?[Aa]nswer\s*:?\s*",
        r".*?[Oo]utput\s*:?\s*",
        r".*?[Rr]esult\s*:?\s*",
        r".*?[Rr]esponse\s*:?\s*",
    ]
    for pattern in strip_patterns:
        content = re.sub(pattern, "", content, flags=re.DOTALL | re.MULTILINE)
        content = content.strip()

    # Step 2: Extract embedded JSON structures
    for pattern in [r"(\{.*\})", r"(\[.*\])"]:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = match.group(1).strip()
            break

    # Step 3: Fix common issues (unquoted identifiers)
    content = re.sub(
        r":\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])",
        r': "\1"\2',
        content,
    )

    # Step 4: Try parsing strategies in preference order
    strategies = [
        lambda c: json.loads(c),
        lambda c: json.loads(json.dumps(ast.literal_eval(c))),
        lambda c: json.loads(c.replace("'", '"')),
        lambda c: json.loads(
            re.sub(
                r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])',
                r': "\1"\2',
                c.replace("'", '"'),
            )
        ),
    ]
    for strategy in strategies:
        try:
            return strategy(content)
        except (json.JSONDecodeError, ValueError, SyntaxError):
            continue

    raise ValueError(f"Could not parse content as JSON: {original_content[:100]}...")


def load_json_data(source: Union[str, Dict, List]) -> Union[Dict, List]:
    """Load JSON from a file path, a JSON string, or return parsed data as-is."""
    if isinstance(source, (dict, list)):
        return source
    if not isinstance(source, str):
        raise TypeError(f"Expected str, dict, or list, got {type(source)}")
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return parse_json_string(source)


# ---------------------------------------------------------------------------
# Core Comparison Utilities
# ---------------------------------------------------------------------------

def normalize_value(v: Any) -> str:
    """Convert a value to a canonical string for comparison."""
    if isinstance(v, float):
        return f"{v:.6f}".rstrip("0").rstrip(".")
    if isinstance(v, bool):
        return str(v).lower()
    if v is None:
        return "none"
    return str(v).strip().lower()


def flatten_json(data: Any, prefix: str = "") -> Dict[str, str]:
    """Recursively flatten nested JSON into dot-notation key-value pairs."""
    if isinstance(data, str):
        try:
            data = parse_json_string(data)
        except ValueError:
            return {prefix: normalize_value(data)}

    flat: Dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)):
                flat.update(flatten_json(value, new_key))
            else:
                flat[new_key] = normalize_value(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            list_key = f"{prefix}[{i}]"
            if isinstance(item, (dict, list)):
                flat.update(flatten_json(item, list_key))
            else:
                flat[list_key] = normalize_value(item)
    return flat


def calculate_similarity_score(gold_val: str, model_val: str) -> float:
    """Return a similarity score in [0, 1] between two normalised values.

    - Exact string match → 1.0
    - Numeric values within tolerance → 0.5–0.9
    - Fallback: character-level Jaccard similarity
    """
    if gold_val == model_val:
        return 1.0

    # Numeric comparison with relative tolerance bands
    try:
        gold_num = float(gold_val)
        model_num = float(model_val)
        if gold_num == 0:
            return 1.0 if model_num == 0 else 0.0
        relative_error = abs(gold_num - model_num) / abs(gold_num)
        if relative_error < 0.01:
            return 0.9
        if relative_error < 0.05:
            return 0.7
        if relative_error < 0.10:
            return 0.5
        return 0.0
    except (ValueError, TypeError):
        pass

    # Character-level Jaccard similarity for strings
    common_chars = set(gold_val) & set(model_val)
    total_chars = set(gold_val) | set(model_val)
    if not total_chars:
        return 1.0
    similarity = len(common_chars) / len(total_chars)
    if gold_val in model_val or model_val in gold_val:
        similarity = max(similarity, 0.6)
    return similarity


# ---------------------------------------------------------------------------
# Evaluation Functions
# ---------------------------------------------------------------------------

def _evaluate_single(
    gold_data: Dict,
    model_data: Dict,
    similarity_threshold: float = 0.0,
    prefix: str = "",
) -> EvaluationResult:
    """Core evaluation logic for a single pair of JSON objects."""
    gold_flat = flatten_json(gold_data)
    model_flat = flatten_json(model_data)

    exact_matches = 0
    total_similarity_score = 0.0
    detailed_results: List[Tuple[str, str, str, bool, str]] = []
    final_exact_matches = 0.0

    gold_keys = set(gold_flat.keys())
    model_keys = set(model_flat.keys())

    if gold_flat == model_flat:
        final_exact_matches += 1.0

    # Evaluate keys present in both sets
    for key in gold_keys & model_keys:
        gold_val = gold_flat[key]
        model_val = model_flat[key]
        similarity = calculate_similarity_score(gold_val, model_val)
        total_similarity_score += similarity
        is_exact = similarity == 1.0
        if is_exact:
            exact_matches += 1
        match_type = (
            "exact"
            if is_exact
            else (
                f"partial ({similarity:.2f})"
                if similarity > similarity_threshold
                else "mismatch"
            )
        )
        detailed_results.append(
            (f"{prefix}{key}", gold_val, model_val, is_exact, match_type)
        )

    # Missing keys (in gold but not model)
    for key in gold_keys - model_keys:
        detailed_results.append(
            (f"{prefix}{key}", gold_flat[key], "MISSING", False, "missing")
        )

    # Extra keys (in model but not gold)
    for key in model_keys - gold_keys:
        detailed_results.append(
            (f"{prefix}{key}", "NOT_IN_GOLD", model_flat[key], False, "extra")
        )

    total_gold_keys = len(gold_flat)
    total_model_keys = len(model_flat)

    precision = exact_matches / total_model_keys if total_model_keys > 0 else 0.0
    recall = exact_matches / total_gold_keys if total_gold_keys > 0 else 0.0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    if total_gold_keys > 0:
        if exact_matches / total_gold_keys == 1.0:
            final_exact_matches = 1.0
    elif gold_flat == model_flat:
        final_exact_matches = 1.0

    return EvaluationResult(
        exact_accuracy=exact_matches / total_gold_keys if total_gold_keys > 0 else 0.0,
        final_exact_accuracy=final_exact_matches,
        partial_score=(
            total_similarity_score / total_gold_keys if total_gold_keys > 0 else 0.0
        ),
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        total_gold_keys=total_gold_keys,
        total_model_keys=total_model_keys,
        matched_keys=len(gold_keys & model_keys),
        exact_matches=exact_matches,
        detailed_results=detailed_results,
    )


def evaluate_json(
    gold_source: Union[str, Dict, List],
    model_source: Union[str, Dict, List],
    similarity_threshold: float = 0.0,
) -> Optional[EvaluationResult]:
    """Evaluate JSON data from various sources (file paths, strings, or objects).

    Returns:
        ``EvaluationResult`` with aggregate metrics, or ``None`` on load error.
    """
    try:
        gold_data = load_json_data(gold_source)
        model_data = load_json_data(model_source)
    except Exception as exc:
        print(f"Error loading JSON data: {exc}")
        return None

    if isinstance(gold_data, list) and isinstance(model_data, list):
        return evaluate_json_lists(gold_data, model_data, similarity_threshold)
    if isinstance(gold_data, dict) and isinstance(model_data, dict):
        return _evaluate_single(gold_data, model_data, similarity_threshold)

    # Normalise mismatched types to lists
    if not isinstance(gold_data, list):
        gold_data = [gold_data]
    if not isinstance(model_data, list):
        model_data = [model_data]
    return evaluate_json_lists(gold_data, model_data, similarity_threshold)


def evaluate_json_files(
    gold_path: str,
    model_path: str,
    similarity_threshold: float = 0.0,
) -> Optional[EvaluationResult]:
    """Load and evaluate two JSON files. Kept for backward compatibility."""
    return evaluate_json(gold_path, model_path, similarity_threshold)


def evaluate_json_lists(
    gold_list: List[Dict],
    model_list: List[Dict],
    similarity_threshold: float = 0.0,
) -> EvaluationResult:
    """Evaluate two parallel lists of JSON objects with proper aggregation."""
    if len(gold_list) != len(model_list):
        print(
            f"Warning: Lists have different lengths. "
            f"Gold: {len(gold_list)}, Model: {len(model_list)}. "
            f"Comparing up to the shorter length."
        )

    total_gold_keys = 0
    total_model_keys = 0
    total_matched_keys = 0
    total_exact_matches = 0
    total_similarity_score = 0.0
    final_exact_matches = 0.0
    all_detailed_results: List[Tuple[str, str, str, bool, str]] = []

    for i, (gold_item, model_item) in enumerate(zip(gold_list, model_list)):
        result = _evaluate_single(
            gold_item, model_item, similarity_threshold, prefix=f"[{i}]."
        )
        total_gold_keys += result.total_gold_keys
        total_model_keys += result.total_model_keys
        total_matched_keys += result.matched_keys
        total_exact_matches += result.exact_matches
        total_similarity_score += result.partial_score * result.total_gold_keys
        all_detailed_results.extend(result.detailed_results)
        final_exact_matches += result.final_exact_accuracy

    precision = (
        total_exact_matches / total_model_keys if total_model_keys > 0 else 0.0
    )
    recall = total_exact_matches / total_gold_keys if total_gold_keys > 0 else 0.0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return EvaluationResult(
        exact_accuracy=(
            total_exact_matches / total_gold_keys if total_gold_keys > 0 else 0.0
        ),
        final_exact_accuracy=final_exact_matches,
        partial_score=(
            total_similarity_score / total_gold_keys if total_gold_keys > 0 else 0.0
        ),
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        total_gold_keys=total_gold_keys,
        total_model_keys=total_model_keys,
        matched_keys=total_matched_keys,
        exact_matches=total_exact_matches,
        detailed_results=all_detailed_results,
    )


def evaluate_datasets(
    gold_file: str,
    model_file: str,
    similarity_threshold: float = 0.0,
) -> Optional[EvaluationResult]:
    """High-level entry point: load datasets and evaluate."""
    gold_dict, model_dict = load_dataset_files(gold_file, model_file)
    if not gold_dict:
        print("No matching data found!")
        return None

    gold_answers = []
    model_answers = []
    for id_ in sorted(gold_dict.keys()):
        gold_answers.append(gold_dict[id_]["Answers"])
        model_answers.append(model_dict[id_]["answer"])

    return evaluate_json(gold_answers, model_answers, similarity_threshold)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def print_detailed_results(
    results: EvaluationResult,
    show_only_mismatches: bool = False,
) -> None:
    """Print a detailed per-key comparison table."""
    print("\nDetailed Results:")
    print("=" * 80)

    entries = results.detailed_results
    if show_only_mismatches:
        entries = [r for r in entries if not r[3]]

    for key, gold_val, model_val, is_exact, match_type in entries:
        if is_exact:
            symbol = "✓"
        elif "partial" in match_type:
            symbol = "~"
        else:
            symbol = "✗"
        print(
            f"{symbol} {key:<40} | Gold: {gold_val:<25} "
            f"| Model: {model_val:<25} | Type: {match_type}"
        )


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python eval_static_score.py <model_output.json>")
        sys.exit(1)

    file_path = sys.argv[1]

    print("\n" + "=" * 80)
    print("Static F1 Evaluation")
    print("=" * 80)

    try:
        results = evaluate_datasets(
            gold_file=REFERENCE_FILE_DEV,
            model_file=file_path,
            similarity_threshold=0.1,
        )
        if results:
            print(results)
    except FileNotFoundError as exc:
        print(f"File not found: {exc}")
        print(
            "Please provide the correct file paths for your "
            "gold standard and model output files."
        )


if __name__ == "__main__":
    main()
