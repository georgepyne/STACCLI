import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Union, cast

import geopandas as gpd
import pandas as pd
import rasterio
from pystac import Item
from shapely.geometry import Polygon, mapping

logger = logging.getLogger(__name__)


def order_stac(items: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        footprint = Polygon(
            [
                [bounds.left, bounds.bottom],
                [bounds.left, bounds.top],
                [bounds.right, bounds.top],
                [bounds.right, bounds.bottom],
            ]
        )

        return cast(List[int], bbox), mapping(footprint), crs


def write_stac_meta(
    file_path: str,
    time: str,
    collection_id: str,
    footprint: Polygon,
    bbox: List[float],
    epsg: str,
    shape: Dict[int, int],
    agg_cloud_cover: float,
) -> None:
    item = Item(
        id=f"{collection_id}_{time}",
        geometry=footprint,
        bbox=bbox,
        datetime=datetime.utcnow(),
        properties={
            "proj:shape": shape,
            "proj:epsg": epsg,
            "eo:agg_cloud_cover": agg_cloud_cover,
        },
    )
    stac_items = json.dumps(
        {"type": "FeatureCollection", "features": [item.to_dict()]},
        indent=4,
    )
    with open(
        os.path.join(file_path, f"{collection_id}_{time}.json"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(stac_items)
