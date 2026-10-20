"""Translate presentation values into backend requests."""
from pathlib import Path
from backend.config import from_fields
from backend.con_interpreter import Controller


class Connections:
    def __init__(self, output=None, controller=None):
        self.controller = controller or Controller()
        self.output = Path(output) if output else Path(__file__).resolve().parents[1] / "output"

    def run(self, fields):
        config = from_fields(fields)
        self.controller.start(config, self.output)

    def cancel(self):
        self.controller.cancel()
