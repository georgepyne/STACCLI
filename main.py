import argparse
from src.stac.planetary_computer_client import query_planetary_computer_stac
from src.stac.stac_parameter_parser import parse_time_window, parse_bbox
from src.stac.stac_utils import order_stac
from src.stac.cog_utils import merge_cogs, clip_cog
import rasterio
from shapely.geometry import box
import pystac
from pyproj import Transformer
from datetime import datetime
import json
import os


def main():
    parser = argparse.ArgumentParser(
        description="List STAC query longitude and latitude bounds: min_lon, min_lat, max_lat, max_lon"
    )
    # configure args
    parser.add_argument("-b", "--bounds", type=str)
    parser.add_argument("-t", "--time", type=str)
    parser.add_argument("-c", "--collection", type=str)
    parser.add_argument("-f", "--file", type=str, default=os.getcwd())
    # parse args
    args = parser.parse_args()
    bounds = parse_bbox(args.bounds)
    time = parse_time_window(args.time)
    collection_id = args.collection
    file_path = args.file
    items = query_planetary_computer_stac(time, bounds, collection_id)
    ordered_features = order_stac(items)
    # open cogs
    cog_urls = [i["assets"]["qa"]["href"] for i in ordered_features]
    cogs = [rasterio.open(i) for i in cog_urls]
    # reproject bounds
    epsg = items["features"][0]["properties"]["proj:epsg"]  # get EPSG code from STAC meta
    transformer = Transformer.from_crs(4326, epsg)
    # merge cogs
    merge_cogs(cogs, file_path, time)
    # transform bbox
    left, bottom, right, top = bounds
    left, bottom, right, top = list(sum([i for i in transformer.itransform([(bottom, left), (top, right)])], ()))
    polygon = box(*[left, bottom, right, top])
    # clip cog
    shape = clip_cog(cogs, polygon, file_path, time)
    # create stac item
    item = pystac.Item(id="local-image-eo",
                       geometry=polygon,
                       bbox=bounds,
                       datetime=datetime.utcnow(),
                       properties={
                           "proj:shape": shape,
                           "proj:epsg": epsg,
                           "eo:agg_cloud_cover": "",
                       })
    stac_items = json.dumps({"type": "FeatureCollection", "features": [item.to_dict()]})
    time = time.replace("/", "-")
    with open(os.path.join(file_path, f"{time}.json"), "w", encoding="utf-8") as f:
        json.dump(stac_items, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
