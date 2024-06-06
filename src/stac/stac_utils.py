import geopandas as gpd
import pandas as pd
from typing import List, Dict


def order_stac(items: dict) -> List[Dict]:
    stac_meta = gpd.GeoDataFrame.from_features(items, crs="epsg:4326")
    stac_meta["datetime"] = pd.to_datetime(stac_meta["datetime"], format="ISO8601")
    stac_meta = stac_meta.sort_values(
        ["eo:cloud_cover", "datetime"], ascending=[False, True]
    )
    ordered_features = [
        items["features"][i] for i in stac_meta.index
    ]  # sort features by cloud cover

    return ordered_features
