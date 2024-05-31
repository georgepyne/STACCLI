from STACCLI.src.stac.stac_parameter_parser import parse_time_window, parse_bbox
from pytest import mark


@mark.parser
def test_time_parser():
    assert isinstance(parse_time_window("2024-04-22/2024-04-29"), str)


@mark.parser
def test_bounds_parser():
    assert isinstance(parse_bbox("-1.066919,52.209855,-1.003834,52.231755"), list)
