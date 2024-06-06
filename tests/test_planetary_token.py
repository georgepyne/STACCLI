import requests
from pytest import mark


@mark.stac
def test_planetary_token():

    result = requests.get(
        "https://planetarycomputer.microsoft.com/api/sas/v1/sign?href=https://naipeuwest.blob.core.windows.net/naip"
        "/01.tif"
    )

    assert result.status_code == 200
