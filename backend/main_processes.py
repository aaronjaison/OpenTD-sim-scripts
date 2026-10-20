"""Coordinate validation, simulation and result publication."""
from .solver import solve, Cancelled
from .results_interp import save_results


def run_trial(config, output, cancelled, progress):
    """Run a preview and return its samples plus the report directory."""
    progress("Validating thermal inputs…")
    samples = solve(config, cancelled, progress)
    if cancelled.is_set():
        raise Cancelled("Trial cancelled; no results published.")
    progress("Saving graph, report and raw samples…")
    folder = save_results(config, samples, output)
    return samples, folder
