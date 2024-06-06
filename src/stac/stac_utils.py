import geopandas as gpd
import pandas as pd
from typing import List, Dict, Iterable, Union
import rasterio
import logging
from shapely.geometry import Polygon, mapping

logger = logging.getLogger(__name__)


def order_stac(items: dict) -> List[Dict]:
    stac_meta = gpd.GeoDataFrame.from_features(items, crs="epsg:4326")
    stac_meta["datetime"] = pd.to_datetime(stac_meta["datetime"], format="ISO8601")
    stac_meta = stac_meta.sort_values(
        ["eo:cloud_cover", "datetime"], ascending=[False, True]
    )
    ordered_features = [
        items["features"][i] for i in stac_meta.index
    ]  # sort features by cloud cover

    return ordered_features


def get_bbox_and_footprint(raster: str) -> Iterable[Union[List[float], Polygon, str]]:
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

        return bbox, mapping(footprint), crs
