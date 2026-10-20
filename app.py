"""Launch the Tkinter workbench with `python app.py`."""
import tkinter as tk
from frontend.interface import Application


def main():
    root = tk.Tk()
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
