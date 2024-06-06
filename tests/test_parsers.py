from pytest import mark
import pytest
from STACCLI.src.stac.stac_parameter_parser import parse_time_window, parse_bbox


@mark.parser
def test_time_parser():
    assert isinstance(parse_time_window("2024-04-22/2024-04-29"), str)


# @mark.parser
def test_bounds_parser():
    def test_bounds():
        bbox = [190, -100, 0, 0]
        if any(
                [
                    ((bbox[0] < -180) | (bbox[0] > 180)),
                    ((bbox[1] < -90) | (bbox[1] > 90)),
                    ((bbox[2] < -180) | (bbox[2] > 180)),
                    ((bbox[3] < -90) | (bbox[3] > 90)),
                ]
        ):
            raise ValueError(
                "Provided bounds are invalid. Bounds must be valid WGS84 coordinates.")

    with pytest.raises(ValueError):
        test_bounds()

