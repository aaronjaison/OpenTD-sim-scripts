"""Vendor adapter contract tests, without starting licensed applications."""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest
from backend import open_td_api as api


def test_discovery(monkeypatch,tmp_path):
    monkeypatch.setenv('OPENTD_HOME',str(tmp_path))
    assert api.find_install()==tmp_path
    monkeypatch.delenv('OPENTD_HOME')
    monkeypatch.setattr(Path,'glob',lambda *_:iter([]))
    with pytest.raises(RuntimeError,match='not found'):api.find_install()
    monkeypatch.setattr(Path,'glob',lambda *_:iter([tmp_path/'OpenTD.dll']))
    assert api.find_install()==tmp_path


@pytest.mark.parametrize('runtime',['netfx','coreclr','bad'])
def test_loading(monkeypatch,tmp_path,runtime):
    monkeypatch.setenv('OPENTD_HOME',str(tmp_path/'Thermal Desktop'))
    monkeypatch.setenv('OPENTD_RUNTIME',runtime)
    modules={name:Mock() for name in ['pythonnet','clr','OpenTD']}
    monkeypatch.setattr(api.importlib,'import_module',lambda name:modules[name])
    monkeypatch.setattr(api.sys,'path',list(api.sys.path))
    if runtime=='bad':
        with pytest.raises(RuntimeError,match='OPENTD_RUNTIME'):api.load_api()
        return
    assert api.load_api() is modules['OpenTD']
    dependency=tmp_path/'TD Designer'/'RemoteExporter'/'Google.Protobuf.dll'
    dependency.parent.mkdir(parents=True);dependency.touch()
    assert api.load_api() is modules['OpenTD']
    assert any('Google.Protobuf.dll' in str(call) for call in modules['clr'].AddReference.call_args_list)
    assert modules['pythonnet'].load.call_args.args[0]==runtime


def test_connect_and_diagnostics(monkeypatch,tmp_path):
    desktop=Mock()
    module=NS(ThermalDesktop=Mock(return_value=desktop),
              TdConnectConfig=NS(Types=NS(START_NEW_TD=7)),Utility=NS(RootedPathname=str))
    monkeypatch.setattr(api,'load_api',lambda:module)
    monkeypatch.setenv('OPENTD_ACAD','C:/AutoCAD/acad.exe')
    assert api.connect(tmp_path/'copy.dwg') is desktop
    assert api.connect(tmp_path/'copy.dwg',module) is desktop
    assert desktop.ConnectConfig.Type==7
    assert desktop.ConnectConfig.StartTimeout.NumberOfTries==120
    assert desktop.ConnectConfig.AcadExePathname=='C:/AutoCAD/acad.exe'
    assert 'OpenTD loaded' in api.diagnostics()


class Arrays:
    def __getitem__(self,_):return list


@pytest.mark.parametrize('fail',[False,True])
def test_read_closes_dataset(monkeypatch,tmp_path,fail):
    dataset=Mock()
    dataset.GetTimes.return_value=[0,1]
    dataset.GetData.return_value=[[293,294]]
    if fail:dataset.GetData.side_effect=ValueError('missing node')
    system=NS(Array=Arrays(),Object=object,String=str,Activator=Mock())
    system.Activator.CreateInstance.return_value=dataset
    modules={'clr':Mock(),'System':system}
    monkeypatch.setattr(api,'load_api',Mock())
    monkeypatch.setattr(api,'assembly_directory',lambda:tmp_path)
    monkeypatch.setattr(api.importlib,'import_module',lambda name:modules[name])
    if fail:
        with pytest.raises(ValueError):api.read_temperatures('trial.sav','MAIN.1')
    else:
        assert api.read_temperatures('trial.sav','MAIN.1')==([0,1],[293,294])
    modules["clr"].AddReference.return_value.GetType.assert_called_once_with("OpenTD.Results.Dataset.SaveFile")
    dataset.GetData.assert_called_once_with(["MAIN.T1"])
    dataset.Units.SetToSI.assert_called_once()
    dataset.Close.assert_called_once()
