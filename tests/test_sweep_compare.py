"""Analytic examples verify alignment, unit conversion and comparison rejection."""
import math
import pytest
from backend.sweep_compare import read_history, interpolate, compare, component_means, write_history


def test_roundtrip_and_metrics(tmp_path):
    path = tmp_path / "nodes.csv"
    write_history(path, [0, 1, 2], {"MAIN.1_temperature_k": [273, 274, 275]})
    reference = read_history(path)
    assert reference[1] == {"MAIN.1": [273, 274, 275]}
    row, = compare(reference, ([0, 2], {"MAIN.1": [274, 276]}))
    assert row["rmse_K"] == row["bias_K"] == row["max_abs_K"] == 1
    row, = compare(([0, 1], {"A": [0, 0]}), ([0, 1], {"A": [-2, 2]}))
    assert row["bias_K"] == 0 and row["rmse_K"] == 2
    assert interpolate([0], [3], [0]) == [3]
    assert interpolate([0, 1], [2, 4], [-1e-8, 1+1e-8]) == [2, 4]
    assert component_means({"A": [273.15], "B": [277.15]}, {"plate": {"A": 1, "B": 3}})["plate"] == [3]


@pytest.mark.parametrize("text", [
    "wrong,A\n0,1", "time_s\n0", "time_s,A,A\n0,1,2",
    "time_s,A\n", "time_s,A\n0,1,2", "time_s,A\n0,nan", "time_s,A\n0,1\n0,2",
])
def test_invalid_csv(tmp_path, text):
    path = tmp_path / "bad.csv"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError): read_history(path)


def test_blank_rows_and_rejections(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("time_s,A\n\n0,1\n", encoding="utf-8")
    assert read_history(path) == ([0.], {"A": [1.]})
    with pytest.raises(ValueError): compare(([0], {"A": [1]}), ([0], {"B": [1]}))
    with pytest.raises(ValueError): interpolate([1, 2], [1, 2], [0, 2])
    with pytest.raises(ValueError): interpolate([0, 1], [1, 2], [0, 2])
    for weights in [{}, {"A": 0}, {"A": math.nan}, {"B": 1}]:
        with pytest.raises(ValueError): component_means({"A": [273.]}, {"plate": weights})
