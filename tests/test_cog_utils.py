import numpy as np
import rasterio
from osgeo_utils.samples import validate_cloud_optimized_geotiff
from pytest import mark
from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.transform import from_origin
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles


@mark.cog
def test_merge_cogs() -> None:
    bounds = [0, 0, 1, 1]  # Create cog bounds
    width = 2
    height = 2
    nbands = 1
    input_raster = np.array([[0, 0], [0, 0]], np.int32)
    target_raster = np.array([[0, 0], [1, 1]], np.int32)
    src_transform = from_origin(*bounds)

    src_profile = dict(
        driver="GTiff",
        dtype="int32",
        count=nbands,
        height=height,
        width=width,
        transform=src_transform,
    )

    with MemoryFile() as mem_file_target:
        with mem_file_target.open(**src_profile) as mem_target:
            mem_target.write(target_raster, 1)
        target_ds = rasterio.open(mem_target.name)

    with MemoryFile() as mem_file_input:
        with mem_file_input.open(**src_profile) as mem_input:
            mem_input.write(input_raster, 1)
        input_ds = rasterio.open(mem_input.name)

    merged, cog_transform = merge([input_ds, target_ds])

    assert np.array_equal(target_raster, merged[0])


@mark.cog
def test_create_cog() -> None:
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
            validate_cloud_optimized_geotiff.validate(mem.name)
            read_array = dataset.read()[0]
            assert np.array_equal(raster_array, read_array)  # validate cog read
