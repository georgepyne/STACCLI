from torchgeo.datasets import VectorDataset, RasterDataset

# set up the label dataset class
class GpkgDataset(VectorDataset):
    filename_glob = "*labels.gpkg"

# initialize the label dataset
label_data = GpkgDataset(
    paths=[
        "/path/to/labels"
    ]
)

class GeoTiffDataset(RasterDataset):
    filename_glob = "*.tif"

# initialize the raster dataset
raster_data = GeoTiffDataset(
    Paths = [
        "/path/to/folder/with/geotif/files",
        "/path/to/another/folder/with/geotif/files",
    ]
)