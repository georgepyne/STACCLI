import json
import os
from datetime import datetime
from typing import List, cast

import numpy as np
import pystac
from pytest import mark
from rasterio import MemoryFile
from rasterio.transform import from_origin
from typing_extensions import assert_type

from ..src.stac.stac_utils import get_bbox_and_footprint, order_stac


@mark.stac
def test_order_stac() -> None:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
    with open(os.path.join(__location__, "test_stac_items.json"), "r") as f:
        items = json.load(f)

    ordered_ids = [
        "LC90350312024114LGN00",
        "LC90350292024114LGN00",
        "LC90350302024114LGN00",
    ]
    ordered_stac_items = order_stac(items)
    ordered_stac_ids = [i["properties"]["landsat:scene_id"] for i in ordered_stac_items]

    assert len(ordered_stac_ids) == len(ordered_ids)
    assert all([a == b for a, b in zip(ordered_stac_ids, ordered_ids)])


@mark.stac
def test_write_stac_meta() -> None:
    bounds = [0, 0, 1, 1]  # Create cog bounds
    width = 2
    height = 2
    nbands = 1

    raster_array = np.array([[0.0, 0.0], [0.0, 0.0]], np.float32)

    src_transform = from_origin(*bounds)

    src_profile = dict(
        driver="GTiff",
        dtype="float32",
        count=nbands,
        height=height,
        width=width,
        transform=src_transform,
    )

    with MemoryFile() as mem_file:
        with mem_file.open(**src_profile) as mem:
            mem.write(raster_array, 1)
            bbox, footprint, crs = get_bbox_and_footprint(mem.name)
            mem.close()

    item = pystac.Item(
        id="test-item",
        geometry=footprint,
        bbox=bbox,
        datetime=datetime.utcnow(),
        properties={},
    )

    item_validation = cast(List[str], item.validate())

    assert assert_type(item_validation, list[str])
    assert len(item_validation) > 0
