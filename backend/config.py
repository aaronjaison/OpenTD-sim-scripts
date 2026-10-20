"""Immutable SI-unit trial inputs and validation."""
from dataclasses import asdict, dataclass
import math
from pathlib import Path
from .equations import parse, evaluate


@dataclass(frozen=True)
class TrialConfig:
    """CAD is a source reference; the preview uses manually supplied properties."""
    model: str = ""
    mass: float = 1.0
    specific_heat: float = 900.0
    area: float = 0.1
    convection: float = 10.0
    emissivity: float = 0.8
    initial: float = 293.15
    ambient: float = 293.15
    duration: float = 600.0
    step: float = 1.0
    heat: str = "25"

    def validate(self):
        # Reject nonfinite inputs before allocating arrays or starting work.
        values = asdict(self)
        for key in values.keys() - {"model", "heat"}:
            if not math.isfinite(values[key]):
                raise ValueError(f"{key} must be finite.")
        for key in ("mass", "specific_heat", "initial", "ambient", "duration", "step"):
            if values[key] <= 0:
                raise ValueError(f"{key} must be greater than zero.")
        if self.area < 0 or self.convection < 0 or not 0 <= self.emissivity <= 1:
            raise ValueError("Area and convection must be nonnegative; emissivity must be 0–1.")
        if self.step > self.duration or self.duration / self.step > 100000:
            raise ValueError("Use a step no larger than duration and at most 100,000 steps.")
        capacity = self.mass * self.specific_heat
        if not math.isfinite(capacity) or capacity <= 0:
            raise ValueError("Combined thermal capacity must be finite and greater than zero.")
        if self.model:
            path = Path(self.model)
            if path.suffix.lower() not in {".sldprt", ".sldasm"} or not path.is_file():
                raise ValueError("Choose an existing .SLDPRT or .SLDASM file.")
        evaluate(parse(self.heat), 0, self.initial, self.ambient)
        return self


def from_fields(fields):
    """Convert UI strings to a validated independent configuration."""
    values = {key: value if key in {"model", "heat"} else float(value)
              for key, value in fields.items()}
    return TrialConfig(**values).validate()
