import importlib.util
from pathlib import Path
from unittest.mock import Mock

SOURCE=Path(__file__).resolve().parents[2] / "corpus/_fetch_qa.py"
def module():
    spec=importlib.util.spec_from_file_location("qa_under_test",SOURCE)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def test_transient_outage_recovers_after_bounded_cooldown(monkeypatch):
    mod=module();clock=[1000.0]
    monkeypatch.setattr(mod.time,"monotonic",lambda:clock[0])
    fetch=Mock(side_effect=[TimeoutError("temporary network outage"),0]);monkeypatch.setattr(mod,"fetch_p5w",fetch)
    assert mod._p5w_guarded("301183","2026-10-04") is None
    clock[0]+=1
    assert mod._p5w_guarded("301205","2026-10-04") is None
    assert fetch.call_count==1
    clock[0]+=181
    assert mod._p5w_guarded("301251","2026-10-04")==0
    assert fetch.call_count==2
    assert mod._p5w_down["v"] is False

def test_permanent_failure_has_a_run_level_probe_cap(monkeypatch):
    mod=module();clock=[1000.0]
    monkeypatch.setattr(mod.time,"monotonic",lambda:clock[0])
    fetch=Mock(side_effect=TimeoutError("still offline"));monkeypatch.setattr(mod,"fetch_p5w",fetch)
    for n in range(8):
        assert mod._p5w_guarded("301183","2026-10-04") is None
        clock[0]+=181
    assert fetch.call_count==4
    assert mod._p5w_down["v"] is True
