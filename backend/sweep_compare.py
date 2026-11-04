"""Compare fresh temperature histories with a reference on its saved time grid."""
import bisect
import csv
import math
from pathlib import Path


def read_history(path):
    """Accept reference headers or workbench node headers; require finite SI data."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        names = [name.removesuffix("_temperature_k") for name in header[1:]]
        if header[0] != "time_s" or not names or len(set(names)) != len(names):
            raise ValueError("Expected time_s and unique temperature columns.")
        rows = [list(map(float, row)) for row in reader if row]
    if not rows or any(len(row) != len(header) for row in rows):
        raise ValueError("Missing or incomplete temperature rows.")
    if any(not math.isfinite(value) for row in rows for value in row):
        raise ValueError("Nonfinite temperature data.")
    times = [row[0] for row in rows]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Times must increase strictly.")
    return times, {name: [row[i+1] for row in rows] for i, name in enumerate(names)}


def interpolate(times, values, targets):
    """Linear interpolation only; prohibit extrapolation beyond roundoff."""
    if targets[0] < times[0]-1e-6 or targets[-1] > times[-1]+1e-6:
        raise ValueError("Fresh run does not cover the full reference interval.")
    result = []
    for target in targets:
        i = max(1, min(bisect.bisect_left(times, target), len(times)-1))
        if len(times) == 1:
            result.append(values[0])
        else:
            fraction = max(0., min(1., (target-times[i-1])/(times[i]-times[i-1])))
            result.append(values[i-1] + fraction*(values[i]-values[i-1]))
    return result


def compare(reference, actual):
    """Return signed bias, RMSE and worst absolute error; never silently drop nodes."""
    rt, rh = reference
    at, ah = actual
    if set(rh) != set(ah):
        raise ValueError("Reference and fresh run have different node/component identities.")
    rows = []
    for name, expected in rh.items():
        observed = interpolate(at, ah[name], rt)
        errors = [a-b for a, b in zip(observed, expected)]
        worst = max(range(len(errors)), key=lambda i: abs(errors[i]))
        rows.append({"name": name, "samples": len(errors),
                     "bias_K": math.fsum(errors)/len(errors),
                     "rmse_K": math.sqrt(math.fsum(e*e for e in errors)/len(errors)),
                     "max_abs_K": abs(errors[worst]), "worst_time_s": rt[worst]})
    return rows


def component_means(histories, weights):
    """Area-weighted means in Celsius; shared IDs contribute their summed areas."""
    means = {}
    for component, mapping in weights.items():
        if not mapping or any(not math.isfinite(w) or w <= 0 for w in mapping.values()):
            raise ValueError("Component area weights must be positive and finite.")
        if not set(mapping) <= set(histories):
            raise ValueError("Component weights reference absent node IDs.")
        total = math.fsum(mapping.values())
        means[component] = [math.fsum(histories[node][i]*w/total for node, w in mapping.items())-273.15
                            for i in range(len(next(iter(histories.values()))))]
    return means


def write_history(path, times, histories):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", *histories])
        writer.writerows([t, *[values[i] for values in histories.values()]] for i, t in enumerate(times))
