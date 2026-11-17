"""Verify relocation touches only a new copy and preserves case physics controls."""
from unittest.mock import Mock, patch
import runpy
import pytest
from backend.ved_bundle import prepare, CASES


def test_prepare_and_cleanup(tmp_path):
    with pytest.raises(ValueError): prepare(tmp_path)
    model = tmp_path / "model"
    model.mkdir()
    for name in ["Recreated_VED_Sweep.dwg", "Materials.tdp", "Optics.rco", *[c+".rco" for c in CASES]]:
        (model / name).write_text("original", encoding="utf-8")
    desktop = Mock()
    with patch("backend.ved_bundle.connect", return_value=desktop):
        drawing = prepare(tmp_path)
    assert drawing != model / drawing.name and drawing.read_text() == "original"
    assert desktop.GetCaseSet.call_count == 6
    assert desktop.GetCaseSet.return_value.OpticFilename == str(model / "VED_e080.rco")
    desktop.Quit.assert_called_once()
    desktop.GetCaseSet.side_effect = RuntimeError("missing case")
    with patch("backend.ved_bundle.connect", return_value=desktop), pytest.raises(RuntimeError):
        prepare(tmp_path)
    assert desktop.Quit.call_count == 2
    assert (model / drawing.name).read_text() == "original"


def test_entrypoint(tmp_path):
    with patch("backend.ved_bundle.prepare", return_value=tmp_path) as prepare_mock:
        with patch("sys.argv", ["ved_bundle", str(tmp_path)]):
            from backend.ved_bundle import main
            main()
        prepare_mock.assert_called_once_with(str(tmp_path))
    with patch("backend.open_td_api.connect"), patch("sys.argv", ["ved_bundle", "missing"]):
        with patch.dict("sys.modules"):
            import sys
            sys.modules.pop("backend.ved_bundle")
            with pytest.raises(ValueError): runpy.run_module("backend.ved_bundle", run_name="__main__")
