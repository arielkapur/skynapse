"""Grid geometry utilities shared by the weather backend and regression tests.

GFS longitude coordinates run from 0 to 360. Leaflet supports an unwrapped
longitude range around the local map centre. Never globally sort wrapped
longitudes: a tile spanning 150..190E would otherwise become -170..179E.
"""
import numpy as np


def split_gfs_longitudes(center_lon, half_width=30.0):
    """Return NOMADS longitude-filter intervals (0..359.75) for a local window."""
    c = float(center_lon) % 360.0
    left, right = c - half_width, c + half_width
    maximum = 359.75
    if left < 0:
        parts = [(left + 360, maximum), (0.0, right)]
    elif right > maximum:
        parts = [(left, maximum), (0.0, right - 360)]
    else:
        parts = [(left, right)]
    return [(round(l, 2), round(r, 2)) for l, r in parts if r >= l]


def unwrap_longitudes(lons, center_lon):
    """Return a continuous geographical X axis around an arbitrary map centre."""
    c = float(center_lon)
    x = np.asarray(lons, dtype=float)
    return c + ((x - c + 180.0) % 360.0) - 180.0


def mercator_latitudes(north_edge, south_edge, height):
    """Geographic latitude at each evenly spaced Web Mercator raster row."""
    north = np.deg2rad(np.clip(north_edge, -85.051128, 85.051128))
    south = np.deg2rad(np.clip(south_edge, -85.051128, 85.051128))
    def y(phi):
        return np.log(np.tan(np.pi/4.0 + phi/2.0))
    yy = y(north) + (np.arange(height) + 0.5) / height * (y(south) - y(north))
    return np.rad2deg(2.0 * np.arctan(np.exp(yy)) - np.pi / 2.0)


def raster_to_mercator(values_north_to_south, source_lats_south_to_north):
    """Resample model image into Mercator pixel rows (not plate carrée rows)."""
    src = np.asarray(values_north_to_south)
    lats = np.asarray(source_lats_south_to_north)
    if src.ndim != 2 or len(lats) != src.shape[0] or len(lats) < 2:
        raise ValueError('Grid must be a 2-D regular latitude raster')
    step = float(np.median(np.diff(lats)))
    north_edge = float(lats[-1] + step/2)
    south_edge = float(lats[0] - step/2)
    target = mercator_latitudes(north_edge, south_edge, src.shape[0])
    fracindex = np.clip((lats[-1]-target)/step,0,len(lats)-1)
    i0=np.floor(fracindex).astype(int)
    i1=np.minimum(i0+1,len(lats)-1)
    f=(fracindex-i0)[:,None]
    return src[i0,:]*(1-f)+src[i1,:]*f
