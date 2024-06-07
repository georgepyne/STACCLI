import argparse
import json
import logging
import os
import sys
from datetime import datetime

import pystac
import rasterio
from pyproj import Transformer
from shapely.geometry import box

from src.cog.cog_utils import clip_cog, merge_cogs
from src.stac.planetary_computer import query_planetary_computer_stac
from src.stac.stac_parameter_parser import parse_bbox, parse_time_window
from src.stac.stac_utils import get_bbox_and_footprint, order_stac

logger = logging.getLogger(__name__)


def main() -> None:
    logger.setLevel(logging.INFO)
    parser = argparse.ArgumentParser(
        description="A CLI tool to query the Microsoft Planetary Computer STAC API to generate a cloud optimized "
        "geotiff and STAC item metadate JSON from a provided collection, bounding box and time window"
    )
    # configure args
    parser.add_argument(
        "-b",
        "--bounds",
        help="WGS84 Bounding box to query STAC in format: min_lon,min_lat,"
        "max_lat,max_lon",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--time",
        help="Time window to query STAC in format: YYYY-MM-DD/YYYY-MM-DD ",
        type=str,
    )
    parser.add_argument(
        "-c", "--collection", help="Collection id to query STAC.", type=str
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to save cog and STAC meta JSON (default: current working "
        "directory)",
        type=str,
        default=os.getcwd(),
    )
    parser.add_argument(
        "-a", "--asset", help="Asset id to query STAC", type=str, default=os.getcwd()
    )

    try:
        # parse args
        args = parser.parse_args()
        bounds = parse_bbox(args.bounds)
        time = parse_time_window(args.time)
        collection_id = args.collection
        file_path = args.directory
        asset = args.asset

        # Get STAC items
        items = query_planetary_computer_stac(time, bounds, collection_id)
        if len(items["features"]) == 0:
            logger.info(f"No STAC items found for: '{bounds}'\n'{time}'")
            sys.exit(0)
        ordered_features = order_stac(items)

        # open cogs
        cog_urls = [i["assets"][asset]["href"] for i in ordered_features]
        cogs = [rasterio.open(i) for i in cog_urls]

        # reproject bounds
        epsg = items["features"][0]["properties"][
            "proj:epsg"
        ]  # get EPSG code from STAC meta
        transformer = Transformer.from_crs(4326, epsg)

        # merge cogs
        time = time.replace("/", "_")
        merge_cogs(cogs, file_path, time, collection_id)

        # transform bbox
        left, bottom, right, top = bounds
        left, bottom, right, top = list(
            sum([i for i in transformer.itransform([(bottom, left), (top, right)])], ())
        )
        polygon = box(*[left, bottom, right, top])

        # clip cog
        shape = clip_cog(cogs, polygon, file_path, time, collection_id)
        agg_cloud_cover = sum(
            [i["properties"]["landsat:cloud_cover_land"] for i in ordered_features]
        ) / len(ordered_features)

        # create STAC item
        bbox, footprint, crs = get_bbox_and_footprint(
            os.path.join(file_path, f"{collection_id}_{time}.tif")
        )
        item = pystac.Item(
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

        sys.exit(0)
    except ValueError as e:
        logger.error(e)
        sys.exit(0)
    except Exception as e:
        logger.error("STAC-CLI error:")
        logger.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
