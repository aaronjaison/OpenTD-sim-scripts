"""Validated SI inputs for the prepared-DWG named-parameter contract."""
from dataclasses import dataclass
import math

# Labels and explanations also define the interface, keeping units consistent.
FIELDS = {
    "initial": ("Initial temperature · K", "Initial temperature of participating thermal nodes; not a fixed boundary." ,293.0),
    "duration": ("Duration · s", "Elapsed simulation time from zero. Ignored when orbit cycles is greater than zero.",3300.0),
    "output": ("Save interval · s", "Interval between saved results; independent of the internal solver time step.",10.0),
    "max_step": ("Maximum solver step · s", "Upper limit on internal transient steps. Verify convergence with smaller steps.",1.0),
    "heat": ("Battery heating · W/m³", "Uniform generation in the prepared battery regions. Typical values: 12000, 20000, 60000, 120000.",12000.0),
    "emissivity": ("Fixed emissivity", "Fixed VED surface emittance, from 0 to 1. Compare 0.35 and 0.85 by queuing separate tests.",0.85),
    "cycles": ("Orbit cycles", "Zero uses Duration; a positive whole number uses cycles multiplied by orbital period.",0.0),
    "period": ("Orbital period · s", "Period of the prepared orbit. Must be consistent with its altitude and orbit definition.",5400.0),
    "altitude": ("Altitude · m", "Altitude of the prepared orbit, in meters above the model's reference body.",400000.0),
    "inclination": ("Inclination · deg", "Orbital inclination, from 0 to 180 degrees.",51.6),
    "beta": ("Beta angle · deg", "Solar beta angle, from -90 to 90 degrees. Use a prepared orbit mode that supports it.",0.0),
}
SYMBOLS = dict(zip(FIELDS, ("SIM_INITIAL_K", "SIM_DURATION_S", "SIM_OUTPUT_S", "SIM_MAX_STEP_S",
    "SIM_BATTERY_QVOL", "SIM_VED_EPS", "SIM_ORBIT_CYCLES", "SIM_ORBIT_PERIOD_S",
    "SIM_ALTITUDE_M", "SIM_INCLINATION_DEG", "SIM_BETA_DEG")))


@dataclass(frozen=True)
class SimulationSettings:
    initial: float = 293.0
    duration: float = 3300.0
    output: float = 10.0
    max_step: float = 1.0
    heat: float = 12000.0
    emissivity: float = 0.85
    cycles: float = 0.0
    period: float = 5400.0
    altitude: float = 400000.0
    inclination: float = 51.6
    beta: float = 0.0
    orbital: bool = False

    def parameters(self):
        values = {name: float(getattr(self, name)) for name in FIELDS}
        if not all(math.isfinite(value) for value in values.values()):
            raise ValueError("Simulation inputs must be finite numbers.")
        if any(values[name] <= 0 for name in ("initial", "duration", "output", "max_step", "period")):
            raise ValueError("Temperatures, times and orbital period must be positive.")
        if self.heat < 0 or not 0 <= self.emissivity <= 1:
            raise ValueError("Heating must be nonnegative and emissivity must be between 0 and 1.")
        if self.cycles < 0 or not values["cycles"].is_integer():
            raise ValueError("Orbit cycles must be a nonnegative whole number.")
        if self.cycles and not self.orbital:
            raise ValueError("Enable orbital settings before selecting orbit cycles.")
        if self.altitude < 0 or not 0 <= self.inclination <= 180 or not -90 <= self.beta <= 90:
            raise ValueError("Check altitude, inclination (0–180) and beta angle (-90–90).")
        end = self.cycles * self.period if self.cycles else self.duration
        if not math.isfinite(end) or max(self.output, self.max_step) > end:
            raise ValueError("Save interval and maximum step must not exceed the finite run duration.")
        values["duration"] = end
        names = list(FIELDS) if self.orbital else list(FIELDS)[:6]
        return {SYMBOLS[name]: format(values[name], ".17g") for name in names}


def apply_settings(desktop, case, settings):
    """Require declared symbols; model authors must wire them into expressions."""
    parameters = settings.parameters()
    available = {str(symbol.Name) for symbol in desktop.GetSymbols()}
    missing = parameters.keys() - available
    if missing:
        raise ValueError("DWG is missing prepared-model symbols: " + ", ".join(sorted(missing)))
    if settings.orbital and not list(case.RadiationTasks):
        raise ValueError("Orbital runs require prepared RadCAD radiation tasks.")
    case.SteadyState, case.Transient = 0, 1
    if settings.orbital:
        case.CalculateRadiation = 1
    return parameters
