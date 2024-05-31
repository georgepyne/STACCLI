import requests
from pytest import mark


@mark.stac
def test_planetary_token():
    """An API unit test function to test client signing of planetary computer endpoint"""

    result = requests.get(
        "https://planetarycomputer.microsoft.com/api/sas/v1/sign?href=https://naipeuwest.blob.core.windows.net/naip/01.tif"
    )

    assert result.status_code == 200
