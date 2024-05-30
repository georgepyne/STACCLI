import argparse


def main():
    parser = argparse.ArgumentParser(
        description="List STAC query longitude and latitude bounds: min_lon, min_lat, max_lat, max_lon"
    )
    parser.add_argument("-b", "--bounds", type=str)
    parser.add_argument("-t", "--time", type=str)
    args = parser.parse_args()
    bounds = args.bounds
    time = args.time
    print(bounds)
    print(time)
    print(f"Query Microsoft Planetary Computer:\nbounds = {bounds}\ntime = {time}")


if __name__ == "__main__":
    main()
