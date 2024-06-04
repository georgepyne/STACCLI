import argparse
from src.stac.planetary_computer_client import query_planetary_computer_stac
from src.stac.stac_parameter_parser import parse_time_window, parse_bbox


def main():
    parser = argparse.ArgumentParser(
        description="List STAC query longitude and latitude bounds: min_lon, min_lat, max_lat, max_lon"
    )
    parser.add_argument("-b", "--bounds", type=str)
    parser.add_argument("-t", "--time", type=str)
    parser.add_argument("-id", "--collection_id", type=str)
    args = parser.parse_args()
    bounds = parse_bbox(args.bounds)
    time = parse_time_window(args.time)
    collection_id = args.collection_id
    items = query_planetary_computer_stac(time, bounds, collection_id)
    print(
        f"Query Microsoft Planetary Computer.\nCollection: {collection_id}\nBounds: {bounds}"
    )
    cog_urls = [i["assets"]["qa"]["href"] for i in items.to_dict()["features"]]
    cogs = [rasterio.open(i) for i in cog_urls]
    with rasterio.open(cog_urls[0]) as src:
        arr = src.read(out_shape=(src.height // 10, src.width // 10))


if __name__ == "__main__":
    main()
