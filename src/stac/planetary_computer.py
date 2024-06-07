import logging
from typing import Any, Dict, List, cast

import planetary_computer
import pystac_client

logger = logging.getLogger(__name__)


def query_planetary_computer_stac(
    time: str, bounds: List[float], collection_id: str
) -> Dict[str, Any]:
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    search = catalog.search(collections=[collection_id], bbox=bounds, datetime=time)
    items = search.get_all_items()

    return cast(Dict[str, Any], items.to_dict())
