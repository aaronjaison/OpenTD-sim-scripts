"""Fourth-order integration of a single lumped thermal body."""
from dataclasses import dataclass
import math
from .equations import parse, evaluate

SIGMA = 5.670374419e-8


class Cancelled(Exception):
    """The user cancelled a trial before publication."""


@dataclass(frozen=True)
class Sample:
    time_s: float
    temperature_k: float
    heat_w: float


def solve(config, cancelled, progress):
    """Solve C*dT/dt = Q(t,T)-h*A*(T-Ta)-e*sigma*A*(T^4-Ta^4)."""
    config.validate()
    expression = parse(config.heat)
    capacity = config.mass * config.specific_heat
    def rate(time, temperature):
        # A physical bound catches unstable steps and invalid equations early.
        if not math.isfinite(temperature) or not 0 < temperature <= 10000:
            raise ValueError("Temperature left 0â€“10,000 K; reduce the step or review inputs.")
        heat = evaluate(expression, time, temperature, config.ambient)
        loss = config.convection * config.area * (temperature - config.ambient)
        loss += config.emissivity * SIGMA * config.area * (temperature**4 - config.ambient**4)
        return (heat - loss) / capacity
    temperature, samples = config.initial, []
    count = math.ceil(config.duration / config.step)
    for index in range(count + 1):
        if cancelled.is_set():
            raise Cancelled("Trial cancelled; no results published.")
        time = min(index * config.step, config.duration)
        rate(time, temperature)
        samples.append(Sample(time, temperature, evaluate(expression, time, temperature, config.ambient)))
        if index < count:
            step = min(config.step, config.duration - time)
            # RK4 evaluates heat at intermediate times for time-varying loads.
            k1 = rate(time, temperature)
            k2 = rate(time + step/2, temperature + step*k1/2)
            k3 = rate(time + step/2, temperature + step*k2/2)
            k4 = rate(time + step, temperature + step*k3)
            temperature += step * (k1 + 2*k2 + 2*k3 + k4) / 6
            if index % max(1, count // 100) == 0:
                progress(f"Solving preview: {int(100 * index / count)}%")
    return samples
