"""Exercise real dropdown widgets, queued discovery and changed drawing handling."""
from unittest.mock import patch
from backend.node_catalog import NodeCatalog
from backend.node_results import ALL_NODES
from frontend.opentd_panel import OpenTDPanel


def test_load_dropdown_and_selection(root, tmp_path):
    panel = OpenTDPanel(root, tmp_path)
    source = tmp_path / "source.dwg"
    source.touch()
    panel.values["drawing"].set(str(source))
    result = NodeCatalog(str(source.resolve()), ("MAIN.1", "MAIN.2"))
    with patch("frontend.opentd_panel.Thread") as thread:
        panel.nodes.load()
        operation = thread.call_args.kwargs["args"][0]
        with patch("frontend.node_picker.discover_nodes", return_value=result) as discover:
            panel.work(operation)
            discover.assert_called_once_with(str(source.resolve()), tmp_path)
    panel.poll()
    assert tuple(panel.nodes.combo["values"]) == (ALL_NODES, *result.nodes)
    assert panel.values["node"].get() == "MAIN.1"
    assert "Loaded 2" in panel.status.get()
    panel.values["node"].set("MAIN.2")
    panel.nodes.accept(result)
    assert panel.values["node"].get() == "MAIN.2"
    panel.values["drawing"].set(str(tmp_path / "other.dwg"))
    assert tuple(panel.nodes.combo["values"]) == (ALL_NODES,) and not panel.values["node"].get()
    assert "ignored" in panel.nodes.accept(result)
    assert tuple(panel.nodes.combo["values"]) == (ALL_NODES,)
    panel.values["drawing"].set(str(source))
    assert "No thermal nodes" in panel.nodes.accept(NodeCatalog(str(source.resolve()), ()))
    assert not panel.values["node"].get()
    panel.close()


def test_invalid_and_failed_load(root, tmp_path):
    panel = OpenTDPanel(root, tmp_path)
    with patch("frontend.node_picker.messagebox.showerror") as error:
        panel.nodes.load()
        error.assert_called_once()
    source = tmp_path / "source.dwg"
    source.touch()
    panel.values["drawing"].set(str(source))
    with patch("frontend.opentd_panel.Thread") as thread:
        panel.check()
        panel.nodes.load()
        assert len(panel.jobs.pending) == 1
        panel.events.put(("done", "available"))
        panel.poll()
        operation = thread.call_args.kwargs["args"][0]
        with patch("frontend.node_picker.discover_nodes", side_effect=RuntimeError("OpenTD unavailable")):
            panel.work(operation)
    panel.poll()
    assert not panel.busy
    assert panel.status.get() == "OpenTD unavailable"
    panel.close()
