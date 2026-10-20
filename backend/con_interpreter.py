"""Worker-to-UI event bridge; workers never call Tkinter."""
from queue import Queue
from threading import Event, Thread
from .main_processes import run_trial
from .solver import Cancelled


class Controller:
    """Allow one worker at a time and communicate through a thread-safe queue."""
    def __init__(self, runner=run_trial):
        self.events = Queue()
        self.cancelled = Event()
        self.worker = None
        self.runner = runner

    @property
    def busy(self):
        return self.worker is not None and self.worker.is_alive()

    def start(self, config, output):
        if self.busy:
            raise ValueError("A trial is already running.")
        self.cancelled.clear()
        self.worker = Thread(target=self._work, args=(config, output), daemon=True)
        self.worker.start()

    def cancel(self):
        self.cancelled.set()

    def _work(self, config, output):
        # Catch worker errors and deliver them to the main Tk event loop.
        try:
            result = self.runner(config, output, self.cancelled,
                                 lambda text: self.events.put(("progress", text)))
            self.events.put(("done", result))
        except Cancelled as error:
            self.events.put(("cancelled", str(error)))
        except Exception as error:
            self.events.put(("error", str(error)))
