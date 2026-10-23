"""Single DWG-to-results window; model, settings and queue share one screen."""
from tkinter import messagebox, ttk
from .connections import Connections
from .graphics import theme
from .opentd_panel import OpenTDPanel


class Application:
    def __init__(self, root, connections=None):
        self.root = root
        self.connections = connections or Connections()
        root.title("ORBIT · Thermal Workbench")
        root.geometry("1120x820")
        root.minsize(900, 760)
        theme(root)
        body = ttk.Frame(root, padding=18)
        body.pack(fill="both", expand=True)
        self.opentd = OpenTDPanel(body, self.connections.output)
        self.opentd.frame.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        # Do not interrupt an active licensed solver or node-discovery operation.
        if self.opentd.busy:
            messagebox.showinfo("OpenTD is running", "Wait for the OpenTD operation to finish before closing.", parent=self.root)
            return
        self.opentd.jobs.clear()
        self.opentd.close()
        self.root.destroy()
