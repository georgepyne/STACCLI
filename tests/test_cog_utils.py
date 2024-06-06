import numpy as np
from osgeo_utils.samples import validate_cloud_optimized_geotiff
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import rasterio
from pytest import mark
@mark.cog
def test_cog_create():
    bounds = [0, 0, 1, 1]  # Create cog bounds

    width = 2
    height = 2
    nbands = 1

    raster_array = np.array([[0, 0], [0, 0]], np.int32)

    src_transform = from_origin(*bounds)

    src_profile = dict(
        driver="GTiff",
        dtype="int32",
        count=nbands,
        height=height,
        width=width,
        transform=src_transform,
    )

    with MemoryFile() as mem_file:
        with mem_file.open(**src_profile) as mem:
            # Populate the input file with numpy array
            mem.write(raster_array, 1)
            dst_profile = cog_profiles.get("deflate")
            cog_translate(
                mem,
                mem.name,
                dst_profile,
                in_memory=True,
                quiet=True,
            )
            mem.close()
        with rasterio.open(mem.name) as dataset:
            read_array = dataset.read()[0]
            v = validate_cloud_optimized_geotiff.validate(mem.name)  # cog validate
            assert np.array_equal(raster_array, read_array)  # validate cog read
