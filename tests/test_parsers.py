import pytest
from pytest import mark

from ..src.stac.stac_parameter_parser import parse_time_window


@mark.stac
def test_time_parser() -> None:
    assert isinstance(parse_time_window("2024-04-22/2024-04-29"), str)


@mark.stac
def test_bounds_parser() -> None:
    def test_bounds() -> None:
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
                "Provided bounds are invalid. Bounds must be valid WGS84 coordinates."
            )

    with pytest.raises(ValueError):
        test_bounds()
