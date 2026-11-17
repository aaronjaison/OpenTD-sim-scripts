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

    selected: tuple[str, ...] | None = None

    def parameters(self):
        # Explicit selections validate only the values the user will override.
        names = list(FIELDS) if self.selected is None else list(self.selected)
        if not names or len(set(names)) != len(names) or set(names) - FIELDS.keys():
            raise ValueError("Select at least one known simulation setting, without duplicates.")
        values = {name: float(getattr(self, name)) for name in names}
        if not all(math.isfinite(value) for value in values.values()):
            raise ValueError("Simulation inputs must be finite numbers.")
        for name in ("initial", "duration", "output", "max_step", "period"):
            if name in values and values[name] <= 0:
                raise ValueError("Temperatures, times and orbital period must be positive.")
        if "heat" in values and values["heat"] < 0:
            raise ValueError("Heating must be nonnegative.")
        if "emissivity" in values and not 0 <= values["emissivity"] <= 1:
            raise ValueError("Emissivity must be between 0 and 1.")
        if "cycles" in values:
            if values["cycles"] < 0 or not values["cycles"].is_integer():
                raise ValueError("Orbit cycles must be a nonnegative whole number.")
            if self.cycles:
                if not self.orbital or "period" not in values:
                    raise ValueError("Enable orbital settings and select period for orbit cycles.")
                values["duration"] = self.cycles * self.period
                if "duration" not in names:
                    names.append("duration")
        for name, low, high in (("altitude", 0, math.inf), ("inclination", 0, 180), ("beta", -90, 90)):
            if name in values and not low <= values[name] <= high:
                raise ValueError("Check altitude, inclination (0-180) and beta angle (-90-90).")
        if not all(math.isfinite(v) for v in values.values()):
            raise ValueError("Run duration must be finite.")
        if "duration" in values and any(values[n] > values["duration"] for n in ("output", "max_step") if n in values):
            raise ValueError("Save interval and maximum step must not exceed the run duration.")
        if self.selected is None and not self.orbital:
            names = list(FIELDS)[:6]
        if self.selected is not None and set(names) & set(list(FIELDS)[6:]) and not self.orbital:
            raise ValueError("Enable orbital settings for selected orbital parameters.")
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
