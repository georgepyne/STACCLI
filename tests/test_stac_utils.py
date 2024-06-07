import json
import os

import geopandas as gpd
import pandas as pd
from pytest import mark


@mark.stac
def test_order_stac() -> None:
    with open(os.path.join(os.getcwd(), "tests", "test_stac_items.json"), "r") as f:
        items = json.load(f)
    order = ["LC90350312024114LGN00", "LC90350292024114LGN00", "LC90350302024114LGN00"]

    stac_meta = gpd.GeoDataFrame.from_features(items, crs="epsg:4326")
    stac_meta["datetime"] = pd.to_datetime(stac_meta["datetime"], format="ISO8601")
    stac_meta = stac_meta.sort_values(
        ["eo:cloud_cover", "datetime"], ascending=[False, True]
    )

    stac_order = [i for i in stac_meta["landsat:scene_id"].to_list()]

    assert order == stac_order
