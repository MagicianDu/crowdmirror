from circe.data.swissmetro import load_swissmetro, SwissmetroRecord


def test_load_swissmetro_returns_records():
    records = load_swissmetro()
    assert len(records) > 1000
    assert isinstance(records[0], SwissmetroRecord)


def test_record_has_required_fields():
    records = load_swissmetro()
    r = records[0]
    assert hasattr(r, "choice")
    assert hasattr(r, "train_tt")
    assert hasattr(r, "train_cost")
    assert hasattr(r, "sm_tt")
    assert hasattr(r, "sm_cost")
    assert hasattr(r, "car_tt")
    assert hasattr(r, "car_cost")
    assert hasattr(r, "purpose")
    assert hasattr(r, "income")


def test_filters_exclude_invalid():
    records = load_swissmetro()
    for r in records:
        assert r.purpose in (1, 3)
        assert r.choice in (1, 2, 3)
