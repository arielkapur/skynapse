import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import self_test
from server import area


def test_local_native_server():
    self_test(check_backend=False)


def test_area_keeps_longitude_near_centre():
    north,south,lon=area(-33.87,151.21)
    assert south < north
    assert lon==151.21
