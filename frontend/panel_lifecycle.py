"""Close child controllers and the workbench poll timer together."""


def close_panel(panel):
    panel.preparation.close()
    panel.setup.close()
    panel.nodes.close()
    panel.cases.close()
    panel.frame.after_cancel(panel.timer)
