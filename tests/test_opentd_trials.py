"""Prepared-case isolation and fresh-result validation."""
from pathlib import Path
import json
from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest
from backend import opentd_trials as trials


class NetList(list):
    def Add(self,item):self.append(item)


@pytest.mark.parametrize('text',['A','1A=2','A=','A=1\na=2'])
def test_bad_overrides(text):
    with pytest.raises(ValueError):trials.parse_overrides(text)


def test_overrides_and_request(tmp_path):
    assert trials.parse_overrides('\n Q = 2+3\n MASS=1')=={'Q':'2+3','MASS':'1'}
    path=tmp_path/'model.dwg';path.touch()
    assert trials.OpenTDRequest(str(path),'Case','MAIN.1').validate().case=='Case'
    for drawing,case,node in [(str(tmp_path/'bad.txt'),'Case','MAIN.1'),
                              (str(tmp_path/'missing.dwg'),'Case','MAIN.1'),
                              (str(path),'','MAIN.1'),(str(path),'Case','bad')]:
        with pytest.raises(ValueError):trials.OpenTDRequest(drawing,case,node).validate()


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    source=tmp_path/'source.dwg';source.write_bytes(b'original model')
    case=Mock(SymbolNames=NetList(['Q']),SymbolValues=NetList(['1']),SymbolComments=NetList(['old']))
    case.Run.side_effect=lambda:(Path(case.UserDirectory)/'trial.sav').touch()
    desktop=Mock();desktop.GetCaseSet.return_value=case
    monkeypatch.setattr(trials.open_td_api,'connect',Mock(return_value=desktop))
    reader=Mock(return_value=([0.,1.],[293.,294.]))
    monkeypatch.setattr(trials.open_td_api,'read_temperatures',reader)
    request=trials.OpenTDRequest(str(source),'Case','MAIN.1',overrides='Q=2\nMASS=5')
    return NS(source=source,case=case,desktop=desktop,reader=reader,request=request,output=tmp_path/'out')


def test_isolated_trial(prepared):
    p=prepared
    samples,folder=trials.run_prepared(p.request,p.output,lambda _:None)
    assert p.source.read_bytes()==b'original model'
    assert p.case.SymbolValues==['2','5']
    assert p.case.SymbolNames==['Q','MASS']
    p.case.Update.assert_called_once();p.case.Run.assert_called_once()
    assert samples[-1].temperature_k==294
    assert (folder/'report.md').is_file()
    config=json.loads((folder/'config.json').read_text())['config']
    assert config['case']=='Case' and 'mass' not in config
    assert 'Preview assumption' not in (folder/'report.md').read_text()
    assert 'OpenTD prepared-case result' in (folder/'report.md').read_text()
    assert (folder/'results.csv').read_text().endswith('1.0,294.0,\n')


@pytest.mark.parametrize('times,temps',[([],[]),([0,1],[293]),([0,float('nan')],[293,294]),
    ([0,1],[293,float('inf')]),([1,0],[293,294]),([0,0],[293,294])])
def test_bad_results(prepared,times,temps):
    prepared.reader.return_value=(times,temps)
    with pytest.raises(ValueError):trials.run_prepared(prepared.request,prepared.output,lambda _:None)


def test_missing_save(prepared):
    prepared.case.Run.side_effect=None
    with pytest.raises(RuntimeError,match='fresh SINDA'):
        trials.run_prepared(prepared.request,prepared.output,lambda _:None)
