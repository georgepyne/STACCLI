import logging
import os
from typing import Dict, List

import geojson
import rasterio
from rasterio import DatasetReader
from rasterio.mask import mask
from rasterio.merge import merge
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


def merge_cogs(
    cogs: List[DatasetReader], path: str, time: str, collection_id: str
) -> None:
    logger.setLevel(logging.INFO)
    time = time.replace("/", "_")
    logger.info("Merging cogs.")
    merged, cog_transform = merge(cogs)
    out_meta = cogs[0].meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "height": merged.shape[1],
            "width": merged.shape[2],
            "transform": cog_transform,
        }
    )
    with rasterio.open(
        os.path.join(path, f"{collection_id}_{time}.tif"), "w", **out_meta
    ) as cog:
        cog.write(merged)


def clip_cog(
    cogs: List[DatasetReader],
    polygon: Polygon,
    path: str,
    time: str,
    collection_id: str,
) -> Dict[int, int]:
    geojson_feature = geojson.Feature(geometry=polygon, properties={})
    cog = rasterio.open(os.path.join(path, f"{collection_id}_{time}.tif"))
    logger.info("Clipping raster.")
    clipped, clip_transform = mask(
        cog, shapes=[dict(geojson_feature["geometry"])], crop=True
    )
    out_meta = cogs[0].meta.copy()
    out_meta.update(
        {
            "driver": "GTiff",
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clip_transform,
        }
    )
    src_profile = dict(
        dtype="int32",
        count=1,
        height=clipped.shape[1],
        width=clipped.shape[2],
        crs="epsg:4326",
        transform=clip_transform,
    )

    with rasterio.open(
        os.path.join(path, f"{collection_id}_{time}.tif"),
        "w",
        **out_meta,
    ) as cog:
        cog.write(clipped)
        cog.close()

    with rasterio.open(
        os.path.join(path, f"{collection_id}_{time}.tif"), "r", **src_profile
    ) as cog:
        dst_profile = cog_profiles.get("deflate")
        cog_translate(
            cog,
            os.path.join(path, f"{collection_id}_{time}.tif"),
            dst_profile,
            in_memory=True,
            quiet=True,
        )  # Translate tif to cog

    return {0: clipped.shape[1], 1: clipped.shape[2]}
