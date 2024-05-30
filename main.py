import argparse


def main():
    parser = argparse.ArgumentParser(
        description="List STAC query bounds: min_lon, min_lat, max_lat, max_lon"
    )
    parser.add_argument("-b", "--bounds", type=str)
    args = parser.parse_args()
    bounds = args.bounds
    print(bounds)


if __name__ == "__main__":
    main()
