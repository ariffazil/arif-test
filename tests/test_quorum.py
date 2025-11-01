from platform.tri_witness.quorum import check_quorum


def test_quorum_passes_when_all_above_threshold():
    passed, score = check_quorum(0.97, 0.98, 0.99)
    assert passed
    assert score >= 0.95


def test_quorum_fails_when_any_witness_below_threshold():
    passed, score = check_quorum(0.97, 0.80, 0.98)
    assert not passed
    assert score < 0.95


def test_quorum_respects_custom_threshold():
    passed, score = check_quorum(0.90, 0.90, 0.90, threshold=0.85)
    assert passed
    assert 0.85 <= score <= 0.90
