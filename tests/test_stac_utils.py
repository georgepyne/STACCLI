import json
import pandas as pd
import geopandas as gpd
from pytest import mark
import os
@mark.stac
def test_order_stac():
    # with open(os.path.join(os.getcwd(), 'tests', 'test_stac_items.json'), 'r') as f:
    with open("/Users/georgepyne/Dev/STACCLI/tests/test_stac_items.json", "r") as f:
        items = json.load(f)
    order = ['LC90350312024114LGN00', 'LC90350292024114LGN00', 'LC90350302024114LGN00']

    stac_meta = gpd.GeoDataFrame.from_features(items, crs="epsg:4326")
    stac_meta["datetime"] = pd.to_datetime(stac_meta["datetime"], format="ISO8601")
    stac_meta = stac_meta.sort_values(
        ["eo:cloud_cover", "datetime"], ascending=[False, True]
    )
    ordered_features = [
        items["features"][i] for i in stac_meta.index
    ]  # sort features by cloud cover

    stac_order = [i for i in stac_meta['landsat:scene_id'].to_list()]

    return order == stac_order
