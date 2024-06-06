from typing import List, Dict

import geojson
import rasterio
from rasterio import DatasetReader
import logging
from rasterio.merge import merge
from rasterio.mask import mask
from shapely.geometry import Polygon
import os

logger = logging.getLogger(__name__)


def merge_cogs(cogs: List[DatasetReader], path: str, time: str) -> None:
    time = time.replace("/", "-")
    print("Merging cogs from STAC. to:")
    print(f"{path}/{time}.tif")
    merged, cog_transform = rasterio.merge.merge(cogs)
    out_meta = cogs[0].meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "height": merged.shape[1],
            "width": merged.shape[2],
            "transform": cog_transform,
        }
    )
    with rasterio.open(f"{path}/{time}.tif", "w", **out_meta) as cog:
        cog.write(merged)


def clip_cog(cogs: List[DatasetReader], polygon: Polygon, path: str, time: str) -> Dict:
    geojson_feature = geojson.Feature(geometry=polygon, properties={})
    gt = rasterio.open(os.path.join(path, f"{time}.tif"))
    clipped, clip_transform = mask(gt, shapes=[dict(geojson_feature["geometry"])], crop=True)
    out_meta = cogs[0].meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clip_transform,
        }
    )
    with rasterio.open(os.path.join(path, f"{time}.tif"), "w", **out_meta) as dest1:
        dest1.write(clipped)

    return {0: clipped.shape[1], 1: clipped.shape[2]}
