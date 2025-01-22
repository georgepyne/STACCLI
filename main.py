import argparse
import logging
import os
import sys
import mercantile
from typing import List, cast
from osgeo import gdal
from pyproj import Transformer
from shapely.geometry import box
from src.stac.planetary_computer import query_planetary_computer_stac
from src.stac.stac_parameter_parser import parse_bbox, parse_time_window
from src.stac.stac_utils import get_bbox_and_footprint, order_stac, write_stac_meta

logger = logging.getLogger(__name__)


def main() -> None:
    logger.setLevel(logging.INFO)
    parser = argparse.ArgumentParser(
        description="A CLI tool to query the Microsoft Planetary Computer STAC API to generate a cloud optimized "
        "geotiff and STAC item metadate JSON from a provided collection, bounding box and time window"
    )
    # configure args
    parser.add_argument(
        "-b",
        "--bounds",
        help="WGS84 Bounding box to query STAC in format: min_lon,min_lat,"
        "max_lon,max_lat",
        type=str,
    )
    parser.add_argument(
        "-p",
        "--pixel",
        help="xyz tile to query STAC in format: x/y/z/p x,y,z tiles specification and p being the pixel zoom level (must be greater than z)",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--time",
        help="Time window to query STAC in format: YYYY-MM-DD/YYYY-MM-DD ",
        type=str,
    )
    parser.add_argument(
        "-c", "--collection", help="Collection id to query STAC.", type=str
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory to save cog and STAC meta JSON (default: current working "
        "directory)",
        type=str,
        default=os.getcwd(),
    )
    parser.add_argument("-a", "--asset", help="Asset id to query STAC", type=str)
    gdal.UseExceptions()
    try:
        from pyproj import datadir

        os.environ["PROJ_LIB"] = (
            "C:\\Users\\Geo\\miniconda3\\envs\\STACCLI\\Library\\share\\proj"
        )
        print(os.environ.get("PROJ_LIB"))

        print(datadir.get_data_dir())

        # parse args
        args = parser.parse_args()
        datadir.set_data_dir(
            "C:\\Program Files\\PostgreSQL\\13\\share\\contrib\\postgis-3.0\\proj\\proj.db"
        )
        print(datadir.get_data_dir())
        bounds = parse_bbox(args.bounds)
        time = parse_time_window(args.time)
        collection_id = args.collection
        file_path = args.directory
        asset = args.asset
        tile = args.pixel
        # insert mvt logic
        x, y, z, p = [int(i) for i in tile.split(",")]
        if 0 <= z <= 24:
            max_tile = mercantile.minmax(z)[1]  # get max tile coord for zoom level
        else:
            raise IndexError(f"Invalid zoom level: {z}")
        if 0 <= x >= max_tile or 0 <= y >= max_tile:  # coord values valid at zoom level
            raise IndexError(
                f"Invalid tile coordinate for zoom level {z}: x={x} y={y}."
            )
        tile = mercantile.Tile(x, y, z)

        if not os.path.exists(file_path):
            logger.exception(f"No such directory: {file_path}")
            sys.exit(0)

        tile_bbox = mercantile.bounds(tile)
        left, bottom, right, top = (
            tile_bbox.west,
            tile_bbox.south,
            tile_bbox.east,
            tile_bbox.north,
        )

        bounds = ",".join(
            [
                str(i)
                for i in [
                    tile_bbox.west,
                    tile_bbox.south,
                    tile_bbox.east,
                    tile_bbox.north,
                ]
            ]
        )

        # Get STAC items
        items = query_planetary_computer_stac(time, bounds, collection_id)
        if len(items["features"]) == 0:
            logger.warning(
                f"No STAC items found for collection '{collection_id}':\n'{asset}'\n'{bounds}'\n'{time}'"
            )
            sys.exit(0)

        # order by cloud cover
        ordered_features = order_stac(items)

        # open cogs
        assets = asset.split(",")
        asset_bands = {assets[i]: i for i in range(len(assets))}
        cog_urls = []

        for feat in ordered_features:
            for a in assets:
                cog_urls = cog_urls + [i["assets"][a]["href"] for i in [feat]]
            # cogs = [rasterio_open(i) for i in cog_urls]
            id = feat["id"]

            outvrt = "/vsimem/stacked.vrt"  # /vsimem is special in-memory virtual "directory"
            # outtif = "/Users/geo/Desktop/test.tif"
            # tifs = cog_urls

            # left, bottom, right, top = bounds

            polygon = box(*[left, bottom, right, top])

            os.environ["PROJ_LIB"] = (
                "C:\\Users\\Geo\\miniconda3\\envs\\STACCLI\\Library\\share\\proj"
            )

            outds = gdal.BuildVRT(outvrt, cog_urls, separate=True)

            # outds = gdal.Translate(outvrt, outds)

            # ST_AddBand(raster torast, raster[], ST_MakeEmptyRaster(integer
            # width, integer
            # height, float8
            # upperleftx, float8
            # upperlefty, float8
            # scalex, float8
            # scaley, float8
            # skewx, float8
            # skewy, integer
            # srid = unknown) ...
            # fromrasts, integer
            # fromband = 1, integer
            # torastindex = at_end)
            # )

            # TODO:
            #### Cloud cover func ######## sprint 1
            # get band rgb as 256*256 array from translate_ds
            # save png to tmp
            # read with cloudgan remove cc
            # cloudgan interpolate (nodataMask, cloudMask if cloudMaskInterpolate)
            # translate mask to cloud band
            ##############################

            #### change detection func #### sprint 1
            # change detect with CSA-CDGAN
            # translate mask to change detection band
            ###############################

            #### object detection func #### sprint 1
            # object detect with torchGeo
            # rasterToVector objects detected
            # write geoJson from STAC item, change geometry to rasterToVector
            ###############################

            #### land cover pred #### sprint 2
            # land cover pred with torchGeo (or other)
            # translate mask to change detection band
            ###############################

            ### change report func ####### sprint 2
            # world2pixel ssi of previous image
            # Change detection %s, area
            # objects in cd area
            # landcover change in cd area
            # cloud cover interpolated
            # no data interpolated

            ### build image storage ### sprint 3/4
            # upload world2pixel ratser to postGIS
            # create stac storage (unprocessed, processed) in supabase upload storage
            # unprocessed storage event -> queue process images to processed storage
            # storage processed storage event ->  queue pgstac update
            # deploy stac api service
            # create aoi for continuous monitoring
            # acl
            # build endpoint -> mpc -> pgstac & supabase storage

            ## UI ## sprint 5/6
            # show map with datrange with layers:
            # rgb, objects, landcover, cd, cc
            # show report dashboard
            # create, update, delete aoi
            # acl

            # for i in range(1, 3):
            #
            #     gdal.FillNodata(
            #         ref.GetRasterBand(i),
            #         None,
            #         1000,
            #         2,
            #         {"INTERPOLATION": "NEAREST"},
            #     )

            # warp_objects
            # gdal.WarpOptions(**wo)

            xres = outds.RasterXSize
            yres = outds.RasterYSize

            outds = gdal.Translate(
                f"{file_path}/{id}.tif",
                outds,
                # dstNodata=-1,
                resampleAlg="bilinear",
                format="COG",
                width=xres,
                height=yres,
            )

            gdal.Warp(
                f"{file_path}/{id}.tif",
                outvrt,
                # errorThreshold
                format="COG",
                cutlineWKT=polygon.wkt,
                cutlineSRS="epsg:4326",
                cropToCutline=True,
                # cutlineBlend
                dstNodata=-1,
                resampleAlg="bilinear",
                width=xres,
                height=yres,
            )

            output_types = [gdal.GDT_Byte, gdal.GDT_UInt16, gdal.GDT_Float32]

            # Define output format and options
            # options = gdal.TranslateOptions(
            #     format="PNG",
            #     bandList=[1, 2, 3],
            #     creationOptions=["WORLDFILE=YES"],
            #     outputType=output_types[1],
            #     width=256,
            #     height=256,
            # )

            # gdal.Translate("C:/Users/Geo/Desktop/testWarp.png", outtif, options=options)

            # # validate cog
            # validate_cloud_optimized_geotiff.validate(
            #     "/Users/geo/Desktop/testWarp.tif", full_check=True
            # )

        # # reproject bounds
        epsg = items["features"][0]["properties"][
            "proj:epsg"
        ]  # get EPSG code from STAC meta
        transformer = Transformer.from_crs(4326, epsg)

        # # merge cogs
        # time = time.replace("/", "_")
        # merge_cogs(cogs, file_path, time, collection_id)

        # # transform bbox
        left, bottom, right, top = bounds
        left, bottom, right, top = list(
            sum([i for i in transformer.itransform([(bottom, left), (top, right)])], ())
        )
        polygon = box(*[left, bottom, right, top])

        # clip cog
        # shape = clip_cog(cogs, polygon, file_path, time, collection_id)

        # create STAC item
        agg_cloud_cover = sum(
            [i["properties"]["landsat:cloud_cover_land"] for i in ordered_features]
        ) / len(ordered_features)
        bbox, footprint, crs = get_bbox_and_footprint(
            os.path.join(file_path, f"{collection_id}_{time}.tif")
        )

        write_stac_meta(
            file_path,
            time,
            collection_id,
            footprint,
            cast(List[float], bbox),
            epsg,
            polygon,
            agg_cloud_cover,
        )
        sys.exit(0)
    except ValueError as e:
        logger.error(e)
        sys.exit(1)
    except Exception as e:
        logger.error("STAC-CLI error:")
        logger.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
