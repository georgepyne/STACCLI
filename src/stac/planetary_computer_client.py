import pystac_client
import planetary_computer
from typing import List
import logging

logger = logging.getLogger(__name__)

def query_planetary_computer_stac(
    time: str, bounds: List[float], collection_id: str
) -> dict:
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    search = catalog.search(collections=[collection_id], bbox=bounds, datetime=time)
    items = search.get_all_items()

    return items.to_dict()
