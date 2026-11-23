import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from grid_geo import split_gfs_longitudes,unwrap_longitudes,raster_to_mercator,mercator_latitudes


def test_dateline_does_not_become_a_world_spanning_raster():
    lon=unwrap_longitudes([130,150,180,181,189],160)
    assert np.allclose(lon,[130,150,180,181,189])
    assert max(lon)-min(lon)<60


def test_western_hemisphere_grid_is_local():
    lon=unwrap_longitudes([297,310,330,357],-33)
    assert np.allclose(lon,[-63,-50,-30,-3])


def test_gfs_parts_cross_zero_meridian():
    assert len(split_gfs_longitudes(1))==2
    assert len(split_gfs_longitudes(-1))==2
    assert len(split_gfs_longitudes(160))==1
    assert len(split_gfs_longitudes(179))==1


def test_mercator_warp_has_correct_orientation_and_limits():
    lat=np.arange(-60,1,0.25)
    raw=np.tile(lat[::-1,None],(1,6))
    warped=raster_to_mercator(raw,lat)
    assert warped.shape==raw.shape
    assert warped[0,0] > warped[-1,0]
    assert abs(warped[0,0]-raw[0,0])<0.3
    assert abs(warped[-1,0]-raw[-1,0])<0.3
    assert not np.allclose(warped,raw)
