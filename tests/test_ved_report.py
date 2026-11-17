"""End-to-end comparison reports use fresh data and preserve input archives."""
import json
import runpy
from unittest.mock import patch
from backend.ved_bundle import CASES
from backend.sweep_compare import write_history
from backend.ved_report import report, main


def test_report_and_cli(tmp_path):
    reference = tmp_path / "reference" / "sweep_data"
    reference.mkdir(parents=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "component_node_weights.json").write_text(json.dumps({"VED": {"MAIN.1": 1}}))
    for case in CASES:
        write_history(reference / (case + "_all_nodes_K.csv"), [0, 1], {"MAIN.1": [273.15, 274.15]})
        write_history(reference / (case + "_component_means_C.csv"), [0, 1], {"VED": [0, 1]})
        write_history(tmp_path / "data" / (case + "_all_nodes_K.csv"), [0, 1], {"MAIN.1": [275.15, 276.15]})
    rows = report(tmp_path)
    assert len(rows) == 12 and all(row["max_abs_K"] == 2 for row in rows)
    assert (tmp_path / "comparison.csv").is_file()
    assert len(json.loads((tmp_path / "node_comparison.json").read_text())) == 6
    with patch("sys.argv", ["ved_report", str(tmp_path)]):
        main()
        with patch.dict("sys.modules"):
            import sys
            sys.modules.pop("backend.ved_report")
            runpy.run_module("backend.ved_report", run_name="__main__")
