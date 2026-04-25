import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from svl_validation import run_sss50, run_svl1_validation


def export_sss50_report():
    report = run_sss50(seed=0, randomized_prompt_order=False)
    with open("tests/sss50_final_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["metrics"], indent=2))
    return report


def export_svl1_report(num_runs=25):
    report = run_svl1_validation(num_runs=num_runs)
    print(json.dumps(report["summary"], indent=2))
    return report


if __name__ == "__main__":
    export_sss50_report()
    export_svl1_report()
