#!/usr/bin/env python3
"""
Check docstring coverage for staged Python files and fail when below threshold.

This script is intended to be run from a git hook (pre-commit). It inspects
staged files (via `git diff --cached --name-only --diff-filter=ACM`) and for
each Python file computes the documentation coverage (PEP-257 docstrings)
using the project's `core` utilities. If any staged file has coverage below
`--threshold` (default 80), the script exits with a non-zero status to block
the commit.
"""
import sys
import subprocess
import argparse
import os
from typing import List

# Import project utilities
try:
    from core.parser import parse_file, get_definitions
    from core.extractor import extract_function_data, extract_class_data
    from core.coverage import coverage_report
except Exception as e:
    print("Error importing project modules:", e)
    sys.exit(2)


def get_staged_files() -> List[str]:
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print("Failed to get staged files:", p.stderr)
        sys.exit(2)
    files = [l.strip() for l in p.stdout.splitlines() if l.strip()]
    return files


def analyze_file(path: str):
    try:
        tree = parse_file(path)
    except Exception as e:
        return None, f"Parse error: {e}"

    classes, functions = get_definitions(tree)
    all_classes = [extract_class_data(c) for c in classes]
    all_functions = []
    for cls in classes:
        for node in cls.body:
            if node.__class__.__name__ == "FunctionDef":
                all_functions.append(extract_function_data(node, class_name=cls.name))
    for func in functions:
        if not any(func in cls.body for cls in classes):
            all_functions.append(extract_function_data(func))

    report = coverage_report(all_functions, all_classes)
    return report, None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=80.0,
                        help="Minimum required docstring coverage percent to allow commit")
    args = parser.parse_args(argv)

    staged = get_staged_files()
    py_files = [f for f in staged if f.endswith('.py')]
    if not py_files:
        # nothing to check
        sys.exit(0)

    failing = []
    for f in py_files:
        if not os.path.exists(f):
            # file may be deleted or renamed in index; skip
            continue
        report, err = analyze_file(f)
        if err:
            print(f"{f}: Error during analysis: {err}")
            failing.append((f, 0.0, err))
            continue
        pct = report.get('coverage_percent', 0.0)
        if pct < args.threshold:
            failing.append((f, pct, None))

    if failing:
        print("\nCommit aborted: Docstring coverage below threshold for staged files:")
        for fname, pct, err in failing:
            if err:
                print(f" - {fname}: ERROR - {err}")
            else:
                print(f" - {fname}: {pct}% (required {args.threshold}%)")
        print("\nPlease improve documentation coverage or stage different files.")
        sys.exit(1)

    # All good
    sys.exit(0)


if __name__ == '__main__':
    main()
