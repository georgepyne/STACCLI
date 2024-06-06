from typing import List
from datetime import datetime
from shapely.geometry import Polygon, mapping
import rasterio
def parse_bbox(bounds: str) -> List[float]:
    try:
        bbox = list(map(float, bounds.split(",")))
        if len(bbox) != 4:
            raise ValueError(
                "Invalid bounding box length. Bounding box requires four bounds: min_lon, min_lat, max_lat, max_lon"
            )

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
    except ValueError as e:
        # log.error(ValueError)
        raise e

    return bbox


def parse_time_window(time: str) -> str:
    try:
        date_format = "%Y-%m-%d"
        time_window = time.split("/")
        if len(time_window) != 2:
            raise ValueError(
                "Invalid time window format. Time paremeter requires two dates in format: YYYY-MM-DD/YYYY-MM-DD"
            )
        [datetime.strptime(t, date_format) for t in time_window]  # ValueError

    except ValueError as e:
        # log.error(ValueError)
        raise e

    return time


def get_bbox_and_footprint(raster: str):
    with rasterio.open(raster) as r:
        crs = r.crs
        bounds = r.bounds
        bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
        footprint = Polygon([
            [bounds.left, bounds.bottom],
            [bounds.left, bounds.top],
            [bounds.right, bounds.top],
            [bounds.right, bounds.bottom]
        ])

        return (bbox, mapping(footprint), crs)