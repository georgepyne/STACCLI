# STAC-CLI

`stac-cli` is a simple command line interface (CLI) tool for querying the [Microsft Planetary Computer](https://planetarycomputer.microsoft.com/) [Spatio-temporal Asset Catalog](https://stacspec.org) (STAC). It is based on the [PySTAC library](https://github.com/stac-utils/pystac).

This CLI accepts a bounding box, time window and collection ID as parameters and will attempt to retrieve data from the Planetary Computer STAC API to clip all available imagery to the provided bounding box and time window. The application will write a [cloud optimised geotiff](https://www.cogeo.org/) (COG) file from the resulting mosaic and a STAC item metadata JSON to describe that COG. 