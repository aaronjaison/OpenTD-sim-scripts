"""Verify process-local compiler setup without invoking an installer."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from backend import toolchain


@pytest.fixture
def environment(monkeypatch,tmp_path):
    monkeypatch.setattr(toolchain.os,'environ',{'ProgramFiles(x86)':str(tmp_path)})
    return tmp_path


def test_existing_environment(monkeypatch,environment):
    monkeypatch.setattr(toolchain.shutil,'which',lambda _: 'link.exe')
    toolchain.os.environ['LIB']='lib'
    toolchain.prepare_toolchain()


def test_missing_locator(monkeypatch,environment):
    monkeypatch.setattr(toolchain.shutil,'which',lambda _:None)
    with pytest.raises(RuntimeError,match='Build Tools'):toolchain.prepare_toolchain()


@pytest.mark.parametrize('mode',['missing_script','success','missing_linker','missing_lib'])
def test_initialization(monkeypatch,environment,mode):
    locator=environment/'Microsoft Visual Studio'/'Installer'/'vswhere.exe'
    locator.parent.mkdir(parents=True);locator.touch()
    installation=environment/'BuildTools'
    script=installation/'Common7'/'Tools'/'VsDevCmd.bat'
    if mode!='missing_script':
        script.parent.mkdir(parents=True);script.touch()
    run=Mock(side_effect=[SimpleNamespace(stdout=str(installation)),
                         SimpleNamespace(stdout='PATH=tools\nLIB=lib\n=ignore\nnoise')])
    monkeypatch.setattr(toolchain.subprocess,'run',run)
    if mode=='missing_lib':run.side_effect=[SimpleNamespace(stdout=str(installation)),SimpleNamespace(stdout='PATH=tools')]
    monkeypatch.setattr(toolchain.shutil,'which',Mock(side_effect=[None,None if mode=='missing_linker' else 'link.exe']))
    if mode=='success':
        toolchain.prepare_toolchain()
        assert toolchain.os.environ['PATH']=='tools' and toolchain.os.environ['LIB']=='lib'
        assert len(run.call_args_list)==2
    else:
        with pytest.raises(RuntimeError):toolchain.prepare_toolchain()
