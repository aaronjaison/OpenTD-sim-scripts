"""Check complete reports, atomic publication and independent trial numbering."""
import csv
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from backend.config import TrialConfig
from backend.solver import Sample
from backend.results_interp import save_results
from backend.plotting import svg,coordinates

ROWS=[Sample(0,293,25),Sample(1,294,25)]


def test_results_and_trial_numbers(tmp_path):
    first=save_results(TrialConfig(),ROWS,tmp_path)
    second=save_results(TrialConfig(),ROWS,tmp_path)
    assert first.name.endswith('trial-0001') and second.name.endswith('trial-0002')
    with (first/'results.csv').open() as stream: records=list(csv.reader(stream))
    assert records==[['time_s','temperature_k','heat_w'],['0','293','25'],['1','294','25']]
    details=json.loads((first/'config.json').read_text())
    assert details['engine']=='Lumped thermal preview'
    assert 'temperature.svg' in (first/'report.md').read_text()
    assert set(p.name for p in first.iterdir())=={'results.csv','report.md','config.json','temperature.svg'}
    source=tmp_path/'x.SLDPRT';source.touch()
    other=save_results(TrialConfig(model=str(source)),ROWS,tmp_path)
    assert other.name.endswith('trial-0001')


def test_reserved_attempt_collision(tmp_path):
    original=Path.mkdir
    collided=False
    def mkdir(path,*args,**kwargs):
        nonlocal collided
        if path.name=='1' and not collided:
            collided=True
            raise FileExistsError()
        return original(path,*args,**kwargs)
    with patch.object(Path,'mkdir',mkdir):
        result=save_results(TrialConfig(),ROWS,tmp_path)
    assert result.name.endswith('trial-0002')


def test_failure_not_published(tmp_path):
    with patch('backend.results_interp.svg',side_effect=OSError('disk full')):
        with pytest.raises(OSError):save_results(TrialConfig(),ROWS,tmp_path)
    assert [p.name for p in tmp_path.iterdir()]==['.trials']


def test_svg_escaping_flat_and_decimation():
    assert '&lt;script&gt;' in svg(ROWS,'<script>')
    assert coordinates([Sample(0,293,0)])==[(60,275)]
    many=[Sample(i,293+i/100,0) for i in range(2003)]
    chart=svg(many,'Long run')
    assert '2002 s' in chart
    assert '730.00,35.00' in chart
