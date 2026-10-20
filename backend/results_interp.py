"""Publish complete, reproducible trial reports in unique output folders."""
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
from .plotting import svg


def save_results(config, samples, output, engine="Lumped thermal preview", metadata=None):
    """Reserve an attempt number atomically; publish only a complete result set."""
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    source = str(Path(config.model).resolve()) if config.model else "manual-body"
    key = hashlib.sha256(source.encode()).hexdigest()[:10]
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(source).stem)[:48]
    prefix = f"{name}_{key}"
    # A per-source reservation avoids duplicate numbering across simultaneous runs.
    reservations = root / ".trials" / prefix
    reservations.mkdir(parents=True, exist_ok=True)
    attempt = len(list(reservations.iterdir())) + 1
    while True:
        try:
            (reservations / str(attempt)).mkdir()
            break
        except FileExistsError:
            attempt += 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = root / f"{stamp}_{prefix}_trial-{attempt:04d}"
    pending = root / f".pending-{target.name}"
    pending.mkdir()
    try:
        with (pending / "results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time_s", "temperature_k", "heat_w"])
            writer.writerows((s.time_s, s.temperature_k, s.heat_w) for s in samples)
        (pending / "temperature.svg").write_text(svg(samples, engine), encoding="utf-8")
        details = {"engine": engine, "source": source, "attempt": attempt,
                   "created_utc": stamp, "config": asdict(config), "metadata": metadata or {}}
        (pending / "config.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
        report = report_text(details, samples)
        (pending / "report.md").write_text(report, encoding="utf-8")
        pending.rename(target)
    except Exception:
        shutil.rmtree(pending)
        raise
    return target


def report_text(details, samples):
    """Embed assumptions, configuration, numerical summary and linked raw data."""
    config = details["config"]
    lines = [f"# {details['engine']}", "", f"Source: `{details['source']}`",
             f"UTC: {details['created_utc']}", f"Trial attempt: {details['attempt']}", "",
             "Preview assumption: one uniform-temperature body. CAD geometry is not parsed or meshed.",
             "For OpenTD results, the prepared drawing defines the physical model and units.", "",
             "![Temperature history](temperature.svg)", "", "## Numerical summary", "",
             f"Samples: {len(samples)}",
             f"Initial temperature: {samples[0].temperature_k:.9g} K",
             f"Final temperature: {samples[-1].temperature_k:.9g} K",
             f"Peak temperature: {max(s.temperature_k for s in samples):.9g} K", "",
             "[All raw samples (CSV)](results.csv)", "", "## Inputs", "", "```json",
             json.dumps(config, indent=2), "```", "", "## Engine metadata", "", "```json",
             json.dumps(details["metadata"], indent=2), "```", ""]
    return "\n".join(lines)
