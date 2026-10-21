"""Verify copied-model discovery, natural ordering and inspection cleanup."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from backend import node_catalog as catalog


def test_discover_unique_sorted_nodes(tmp_path, monkeypatch):
    source = tmp_path / "source.dwg"
    source.write_bytes(b"original")
    desktop = Mock()
    desktop.GetNodes.return_value = [SimpleNamespace(Submodel=name, Id=number)
        for name, number in [("MAIN", 10), ("MAIN", 2), ("MAIN", 2), ("A", 1)]]
    connect = Mock(return_value=desktop)
    monkeypatch.setattr(catalog.open_td_api, "connect", connect)
    result = catalog.discover_nodes(str(source), tmp_path / "output")
    assert result == catalog.NodeCatalog(str(source.resolve()), ("A.1", "MAIN.2", "MAIN.10"))
    copy = connect.call_args.args[0]
    assert copy != source and copy.read_bytes() == b"original"
    assert source.read_bytes() == b"original"
    desktop.Quit.assert_called_once()
    desktop.SaveAs.assert_not_called()


@pytest.mark.parametrize("failure", [False, True])
def test_empty_and_failed_discovery_close(tmp_path, monkeypatch, failure):
    source = tmp_path / "source.dwg"
    source.touch()
    desktop = Mock()
    desktop.GetNodes.return_value = []
    if failure:
        desktop.GetNodes.side_effect = RuntimeError("Unable to read nodes")
    monkeypatch.setattr(catalog.open_td_api, "connect", lambda _: desktop)
    if failure:
        with pytest.raises(RuntimeError, match="Unable to read"):
            catalog.discover_nodes(str(source), tmp_path)
    else:
        assert catalog.discover_nodes(str(source), tmp_path).nodes == ()
    desktop.Quit.assert_called_once()


@pytest.mark.parametrize("name", ["missing.dwg", "wrong.txt", ""])
def test_invalid_drawing(tmp_path, name):
    with pytest.raises(ValueError, match="existing"):
        catalog.validate_drawing(str(tmp_path / name))
