"""Reuse complete matching reports, or explicitly execute a fresh trial."""
import csv
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from .solver import Sample
from .node_results import ALL_NODES


def identity(config):
    """Hash direct input files and default DWG databases with the configuration."""
    settings = asdict(config)
    source = settings.get("drawing", settings.get("model", ""))
    paths = [Path(source)] if source else []
    if "drawing" in settings:
        paths += [Path(source).with_name(name) for name in ("TdThermo.tdp", "RcOptics.rco")]
    files = {}
    for path in paths:
        if path.is_file():
            with path.open("rb") as stream:
                files[str(path.resolve())] = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"config": settings, "files": files}


def read_samples(folder):
    """Reject incomplete or corrupt exports instead of presenting them as results."""
    with (folder / "results.csv").open(encoding="utf-8", newline="") as stream:
        samples = [Sample(float(row["time_s"]), float(row["temperature_k"]),
                          float(row["heat_w"]) if row["heat_w"] else None)
                   for row in csv.DictReader(stream)]
    if not samples or any(not math.isfinite(s.time_s + s.temperature_k) for s in samples):
        raise ValueError("Invalid saved samples")
    return samples


def reuse_or_run(config, output, operation, progress, force=False):
    """Newest complete exact match wins; reruns always publish another attempt."""
    key = identity(config)
    root = Path(output)
    if not force:
        for record in sorted(root.glob("*/config.json"), reverse=True):
            folder = record.parent
            receipt = folder / "reuse.json"
            try:
                if receipt.exists():
                    matches = json.loads(receipt.read_text(encoding="utf-8")) == key
                else:
                    # Older exports lack fingerprints: only accept unchanged direct inputs.
                    details = json.loads(record.read_text(encoding="utf-8"))
                    matches = details["config"] == key["config"] and all(
                        Path(path).stat().st_mtime <= record.stat().st_mtime for path in key["files"])
                if not matches:
                    continue
                required = ["report.md", "temperature.svg", "config.json"]
                if key["config"].get("node") == ALL_NODES:
                    required += ["nodes.csv", "node_summary.csv"]
                if not all((folder / name).is_file() for name in required):
                    continue
                samples = read_samples(folder)
            except (OSError, ValueError, KeyError, TypeError):
                continue
            progress(f"Loaded saved results: {folder.name}")
            return samples, folder
    samples, folder = operation()
    (folder / "reuse.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    return samples, folder
