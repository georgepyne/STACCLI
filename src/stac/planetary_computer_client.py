import pystac_client
import planetary_computer


def query_planetary_computer_stac(time: str, bounds: str) -> None:
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    bbox = [-1.066919, 52.209855, -1.003834, 52.231755]

    search = catalog.search(collections=["landsat-c2-l2"], bbox=bbox, datetime=time)
    items = search.get_all_items()
