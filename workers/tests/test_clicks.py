import pytest

from workers.common.clicks import ClickError, check_bounds, object_id, parse_clicks


def test_objects_and_refinements():
    assert parse_clicks(["10,20", "11,21,-", "12,22,+", "30,40"]) == [
        [(10.0, 20.0, True), (11.0, 21.0, False), (12.0, 22.0, True)],
        [(30.0, 40.0, True)],
    ]


@pytest.mark.parametrize("spec", ["10", "a,b", "1,2,x", "1,2,3,4", "", "1,,2"])
def test_malformed_specs_raise(spec):
    with pytest.raises(ClickError):
        parse_clicks([spec])


@pytest.mark.parametrize("spec", ["1,2,-", "1,2,+"])
def test_refinement_without_object_raises(spec):
    with pytest.raises(ClickError):
        parse_clicks([spec])


def test_bounds():
    check_bounds([[(0, 0, True), (99.5, 49.5, True)]], 100, 50)
    for x, y in [(-1, 0), (0, -0.1), (100, 0), (0, 50), (5000, 5000)]:
        with pytest.raises(ClickError):
            check_bounds([[(x, y, True)]], 100, 50)


def test_object_ids_follow_click_order():
    assert [object_id(i) for i in (1, 2, 10)] == ["obj-01", "obj-02", "obj-10"]
