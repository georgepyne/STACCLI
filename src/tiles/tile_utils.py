import json
import logging
from typing import Dict, List, Union, Any, Tuple, Callable

import morecantile
import numpy.typing as npt
import rasterio
from affine import Affine
from geojson_pydantic import Feature, FeatureCollection, Polygon
from morecantile import Tile
from morecantile.errors import InvalidIdentifier
from rasterio import DatasetReader
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from shapely import to_geojson
from shapely.geometry import box
from supermorecado import burnTiles

from src.cog.cog_utils import clip_cog

logger = logging.getLogger(__name__)


def set_xyz_grid(
    geometry: Union[List[Feature[Polygon, Dict]], List[float]],
    tile_matrix_set: str = "WebMercatorQuad",
    tile_zoom_level: int = 18,
    pixel_zoom_level: int = 24,
) -> npt.NDArray[Any]:
    """
    A method to construct XYZ tile cells useful for aggregating aerial imagery that may not have
    orientation, resolution and bounded alignment.
    If a GeoJSON geometry is provided the resulting grid will return only intersecting tiles.

    Parameters
    ----------
    tile_matrix_set : str
        A default TileMatrixSet supported by morecantile (options are CDB1GlobalGrid, CanadianNAD83_LCC,
        EuropeanETRS89_LAEAQuad, GNOSISGlobalGrid, LINZAntarticaMapTilegrid, NZTM2000Quad,
        UPSAntarcticWGS84Quad, UPSArcticWGS84Quad, UTM31WGS84Quad, WebMercatorQuad, WGS1984Quad,
        WorldCRS84Quad, WorldMercatorWGS84Quad)
    tile_zoom_level : int
        The TileMatrixSet zoom level to set as orbital grid cell size.
    pixel_zoom_level : int
        The TileMatrixSet zoom level to set grid cell pixel size.
    geometry : dict
        A GeoJSON feature to select intersecting tiles.

    Returns
    -------
    array-like
        A list of XYZ tiles that intersect the given geometry.
    """
    try:
        if pixel_zoom_level <= tile_zoom_level:
            raise ValueError(
                f"Pixel zoom level must be greater than tile zoom level:\
                 tile zoom: {tile_zoom_level} pixel zoom: {pixel_zoom_level}"
            )
        tms = morecantile.tms.get(tile_matrix_set)
        burn_tiles = burnTiles(tms=tms)
        if isinstance(geometry, list):
            tiles = burn_tiles.burn(
                parse_bbox_(geometry), tile_zoom_level
            )  # raises ValueError
        else:
            tiles = burn_tiles.burn(geometry, tile_zoom_level)  # raises ValueError
        return tiles
    except (InvalidIdentifier, OverflowError) as e:
        logger.error(f"Error creating TileMatrixSet: {e}")
        raise e
    except (ValueError, TypeError) as e:
        logger.error(e)
        raise e


def parse_bbox_(bbox: Union[List[float], npt.NDArray[float]]) -> FeatureCollection:
    """
    A helper function to parse a list of WGS84 coordinates: min_lon, min_lat, max_lat, max_lon.

    Parameters
    ----------
    bbox: array-like
        A list of four of WGS84 coordinates: min_lon, min_lat, max_lat, max_lon.


    Returns
    -------
    FeatureCollection
        A GeoJSON-like feature collection containing the bbox polygon.

    """
    if len(bbox) != 4:
        raise IndexError(
            "Invalid bounding box length. Bounding box requires four bounds: min_lon, min_lat, max_lat, max_lon."
        )

    if any(
        [
            ((bbox[0] < -180) | (bbox[0] > 180)),
            ((bbox[1] < -90) | (bbox[1] > 90)),
            ((bbox[2] < -180) | (bbox[2] > 180)),
            ((bbox[3] < -90) | (bbox[3] > 90)),
        ]
    ):
        raise ValueError(
            "Provided bounds are invalid. Bounds must be valid WGS84 coordinates."
        )

    feature = Feature(**json.loads(to_geojson(box(*bbox))))

    return FeatureCollection(type="FeatureCollection", features=[feature])


def get_tile_pixel_resolution(
    x_shape: int,
    y_shape: int,
    tile: Tile,
    tile_matrix_set: str = "WebMercatorQuad",
    precision: Union[int, None] = None,
) -> Tuple[float, float]:
    """
    A method for generating an x and y pixel resolution from an expected number
    of pixels for both axes. This method can be used to generate pixel resolutions that
    fit within the bounds of an XYZ tile in its native unit of measurement.

    Parameters
    ----------
    x_shape : int
        The number of x-axis pixels (or columns) for generating a raster from XYZ tile.
    y_shape : int
    The number of x-axis pixels (or rows) for generating a raster from XYZ tile.
    tile : morecantile.Tile
        A instance of a XYZ morecantile tile.
    tile_matrix_set : str
        A default TileMatrixSet supported by morecantile.
    precision : int | None
        A precision argument for pixel resolution size of a given XYZ tile.

    Returns
    -------

    """
    try:
        tms = morecantile.tms.get(tile_matrix_set)
        bounds = tms.xy_bounds(tile)
        x_res = abs(bounds.left - bounds.right) / x_shape
        y_res = abs(bounds.bottom - bounds.top) / y_shape

        if precision:
            x_res, y_res = round(x_res, precision), round(y_res, precision)

        return x_res, y_res

    except (InvalidIdentifier, OverflowError) as e:
        logger.error(f"Error creating TileMatrixSet: {e}")
        raise e
    except (ValueError, TypeError) as e:
        logger.error(e)
        raise e


def warp_raster_to_xyz_tile_set(
    x_shape: int,
    y_shape: int,
    tile: Tile,
    image: DatasetReader,
    tms: morecantile.tms,
    resampling: Union[Resampling, str],
    write_cog: Callable = clip_cog,
    *args,
    **kwargs,
):
    """
    A method to resample aerial imagery pixels to a XYZ tile with a given x and y pixel resolution.
    This is useful for comparing aerial images with different capture dates which may have different
    orientations, bounds and pixel resolutions. Using XYZ tiles it is possible to generate standardized
    raster bounds and pixels to enable historical comparisons between aerial images. Resampling of
    raster pixels is achieved through the gdal warp function (see :https://gdal.org/en/stable/programs/gdalwarp.html).

    Parameters
    ----------
    image : rasterio.DatasetReader
    x_shape : int
    y_shape : int
    tile : morcantile.Tile

    Returns
    -------

    """
    try:
        if isinstance(resampling, str):
            resampling = getattr(Resampling, resampling)

        with WarpedVRT(
            image, crs=f"EPSG:{tms.crs.to_epsg()}", resampling=resampling
        ) as vrt:
            # Determine the destination tile and its mercator bounds using
            # functions from the mercantile module.
            # dst_tile = mercantile.tile(*vrt.lnglat(), 9)
            left, bottom, right, top = tile
            polygon = box(*[left, bottom, right, top])

            # Determine the window to use in reading from the dataset.
            dst_window = vrt.window(left, bottom, right, top)

            # Read into a 3 x 512 x 512 array. Our output tile will be
            # 512 wide x 512 tall.
            data = vrt.read(window=dst_window, out_shape=(3, x_shape, y_shape))

            # Use the source's profile as a template for our output file.
            profile = vrt.profile
            profile["width"] = x_shape
            profile["height"] = y_shape
            profile["driver"] = "GTiff"

            # We need determine the appropriate affine transformation matrix
            # for the dataset read window and then scale it by the dimensions
            # of the output array.
            dst_transform = vrt.window_transform(dst_window)
            scaling = Affine.scale(
                dst_window.height / x_shape, dst_window.width / y_shape
            )
            dst_transform *= scaling
            profile["transform"] = dst_transform

            profile["polygon"] = box(*[left, bottom, right, top])
            wite_arguments = {**kwargs, **profile}
            write_cog(**wite_arguments)

        return None
    except AttributeError as e:
        logger.error(e)
        raise e
