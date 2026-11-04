"""Recompute the six-case comparison from a study bundle's exported CSVs."""
import argparse
import csv
import json
import math
from pathlib import Path
from .sweep_compare import read_history, compare, component_means, write_history
from .ved_bundle import CASES


def report(bundle):
    root = Path(bundle)
    weights = json.loads((root / "component_node_weights.json").read_text(encoding="utf-8"))
    summaries, details = [], []
    for case in CASES:
        reference = root / "reference" / "sweep_data"
        actual = read_history(root / "data" / (case + "_all_nodes_K.csv"))
        node_rows = compare(read_history(reference / (case + "_all_nodes_K.csv")), actual)
        worst = max(node_rows, key=lambda row: row["max_abs_K"])
        summary = {"case": case, "series": "ALL_NODES", "max_abs_K": worst["max_abs_K"],
                   "rmse_K": math.sqrt(math.fsum(r["rmse_K"]**2 for r in node_rows)/len(node_rows)),
                   "bias_K": math.fsum(r["bias_K"] for r in node_rows)/len(node_rows),
                   "worst_time_s": worst["worst_time_s"], "worst_node": worst["name"]}
        summaries.append(summary)
        details.extend(dict(case=case, **row) for row in node_rows)
        means = component_means(actual[1], weights)
        write_history(root / "data" / (case + "_component_means_C.csv"), actual[0], means)
        rows = compare(read_history(reference / (case + "_component_means_C.csv")), (actual[0], means))
        for row in rows:
            summaries.append({"case": case, "series": row["name"], "max_abs_K": row["max_abs_K"],
                              "rmse_K": row["rmse_K"], "bias_K": row["bias_K"],
                              "worst_time_s": row["worst_time_s"], "worst_node": "area mean"})
    (root / "comparison.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    (root / "node_comparison.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
    with (root / "comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    args = parser.parse_args()
    report(args.bundle)
    print(f"Comparison saved in {Path(args.bundle).resolve()}")


if __name__ == "__main__":
    main()
