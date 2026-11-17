"""Validate all-node histories and export an equally weighted node average."""
import csv
import math
from .solver import Sample

ALL_NODES = "All nodes"
AVERAGE_DESCRIPTION = ("Arithmetic mean across unique saved thermal node IDs at each time, "
                       "including boundary nodes. Shared-temperature IDs count once. "
                       "This is not a mass-, area-, or heat-capacity-weighted temperature.")


def summarize(times, histories):
    """Require a complete common time grid; never silently omit missing nodes."""
    if not times or not histories:
        raise ValueError("No all-node temperature results were returned.")
    if any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Result times must be finite and strictly increasing.")
    for values in histories.values():
        if len(values) != len(times) or any(not math.isfinite(value) for value in values):
            raise ValueError("Every node must have a finite temperature at every result time.")
    count = len(histories)
    rows = []
    for index, time in enumerate(times):
        temperatures = [values[index] for values in histories.values()]
        mean = math.fsum(value / count for value in temperatures)
        rows.append((time, mean, min(temperatures), max(temperatures), count))
    return rows


def mean_samples(summary):
    return [Sample(row[0], row[1], None) for row in summary]


def write_node_files(folder, times, histories, summary):
    """Stream wide histories and summary into the unpublished report folder."""
    with (folder / "nodes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", *[f"{node}_temperature_k" for node in histories]])
        writer.writerows([time, *[values[index] for values in histories.values()]]
                         for index, time in enumerate(times))
    with (folder / "node_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "average_temperature_k", "minimum_temperature_k",
                         "maximum_temperature_k", "node_count"])
        writer.writerows(summary)
    return ("\n## All-node temperatures\n\n" + AVERAGE_DESCRIPTION +
            "\n\nThe graph and results.csv show this mean over time.\n\n"
            "[Individual node histories (K)](nodes.csv) · "
            "[Mean, minimum and maximum over time (K)](node_summary.csv)\n")
