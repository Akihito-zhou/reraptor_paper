from paper.experiments import check_reproduction as checker


def test_public_clone_does_not_require_private_inputs(tmp_path):
    assert checker.check_inputs(tmp_path) == []
    assert len(checker.check_inputs(tmp_path, require_data=True)) == 6


def test_partial_or_changed_private_input_is_rejected(tmp_path):
    path = tmp_path / next(iter(checker.PLANNER_INPUTS))
    path.parent.mkdir(parents=True)
    path.write_text("not a private dataset", encoding="utf-8")
    errors = checker.check_inputs(tmp_path)
    assert len(errors) == 6
    assert any("mismatch" in error for error in errors)
    assert sum("Missing" in error for error in errors) == 5


def test_exact_identity_and_ambiguous_snapshot(tmp_path, monkeypatch):
    import hashlib
    relative = "apps/api/data/timetables/segments_fukuoka_20251224.csv"
    content = b"synthetic test only"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    monkeypatch.setattr(checker, "PLANNER_INPUTS", {
        relative: (len(content), hashlib.sha256(content).hexdigest())
    })
    assert checker.check_inputs(tmp_path, require_data=True) == []
    path.with_name("segments_fukuoka_20990101.csv").write_bytes(content)
    assert len(checker.check_inputs(tmp_path, require_data=True)) == 1


def test_missing_inputs_cannot_be_reported_as_a_solver_run(tmp_path, monkeypatch):
    import pytest
    from paper.experiments.common import planner_bridge
    monkeypatch.setattr(planner_bridge, "PLANNER_DATA_DIR", tmp_path)
    monkeypatch.setattr(planner_bridge, "_planner_instance", None)
    with pytest.raises(RuntimeError, match="empty network"):
        planner_bridge.load_planner(force_reload=True)
    assert planner_bridge._planner_instance is None
