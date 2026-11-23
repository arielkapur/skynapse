#!/usr/bin/env python3
"""SkySynoptic local forecast server: actual regional GFS GRIB2 grids."""
import json, os, sys, time, threading, urllib.parse, urllib.request, webbrowser
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import numpy as np
import xarray as xr
from scipy.ndimage import gaussian_filter
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from grid_geo import split_gfs_longitudes, unwrap_longitudes, raster_to_mercator

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
CACHE=Path.home()/'Library'/'Caches'/'SkySynoptic' if sys.platform=='darwin' else Path.home()/'.cache'/'skysynoptic'
CACHE.mkdir(parents=True,exist_ok=True)
# Do not serialize *every* request behind one slow NOAA download.
DOWNLOAD_SLOTS=threading.Semaphore(3)
UA='SkySynoptic/1.3 (personal local weather visualization)'
FIELDS={'pressure':('PRMSL','mean_sea_level'),'cloud':('TCDC','entire_atmosphere'),'temp':('TMP','2_m_above_ground'),'humidity':('RH','2_m_above_ground'),'rain':('APCP','surface')}

def cycle_candidates():
    now=datetime.now(timezone.utc)
    for h in (6,12,18,24,30,36,42,48):
        d=now-timedelta(hours=h)
        yield d.replace(hour=d.hour//6*6,minute=0,second=0,microsecond=0)

def area(lat,lon):
    lat=max(-65,min(65,float(lat)))
    lon=float(lon)
    return (round(min(85,lat+23),2),round(max(-85,lat-23),2),lon)

def download(field,fh,bbox,cycle):
    variable,level=FIELDS[field]
    stamp=cycle.strftime('%Y%m%d');cc=cycle.strftime('%H')
    left,right,top,bottom=bbox
    key=f'{stamp}_{cc}_{field}_{fh}_{left}_{right}_{top}_{bottom}'.replace('.','p')
    file=CACHE/(key+'.grib2')
    if file.exists() and file.stat().st_size>1000:return file
    params={'file':f'gfs.t{cc}z.pgrb2.0p25.f{fh:03d}',f'var_{variable}':'on',f'lev_{level}':'on','subregion':'','leftlon':str(left),'rightlon':str(right),'toplat':str(top),'bottomlat':str(bottom),'dir':f'/gfs.{stamp}/{cc}/atmos'}
    url='https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with DOWNLOAD_SLOTS:
        with urllib.request.urlopen(req,timeout=55) as r: data=r.read(20_000_000)
    if not data.startswith(b'GRIB') or len(data)<1000:raise RuntimeError('NOAA returned no valid '+field+' GRIB')
    tmp=file.with_suffix('.part')
    tmp.write_bytes(data)
    tmp.replace(file)
    return file

def grid(file,field,center_lon):
    ds=xr.open_dataset(str(file),engine='cfgrib',backend_kwargs={'indexpath':''})
    try:
        arr=next(iter(ds.data_vars.values()))
        values=np.asarray(arr.values,dtype=float).squeeze()
        lats=np.asarray(arr.latitude.values,dtype=float)
        lons=np.asarray(arr.longitude.values,dtype=float)
        if lats.ndim!=1 or lons.ndim!=1 or values.ndim!=2:raise ValueError('Unexpected GRIB grid geometry')
        if lats[0]>lats[-1]:lats=lats[::-1];values=values[::-1,:]
        if lons[0]>lons[-1]:lons=lons[::-1];values=values[:,::-1]
        if field=='pressure':values/=100
        if field=='temp':values-=273.15
        # Retain *continuous* longitudes around the viewport centre.
        lons=unwrap_longitudes(lons,center_lon)
        order=np.argsort(lons);lons=lons[order];values=values[:,order]
        return values,lats,lons
    finally:ds.close()

def make_frame(field,fh,bbox,cycle):
    stamp=cycle.strftime('%Y%m%d_%H');key=f'{stamp}_{field}_{fh}_'+('_'.join(map(str,bbox))).replace('.','p')
    result_path=CACHE/(key+'.json');image_path=CACHE/(key+'.png')
    if result_path.exists() and image_path.exists():return json.loads(result_path.read_text())
    north,south,center_lon=bbox
    pieces=[]
    for left,right in split_gfs_longitudes(center_lon):
        filepath=download(field,fh,(left,right,north,south),cycle)
        pieces.append(grid(filepath,field,center_lon))
    lats=pieces[0][1]
    if any(not np.allclose(part[1],lats) for part in pieces[1:]):
        raise ValueError('GFS subgrids have incompatible latitudes')
    vals=np.concatenate([part[0] for part in pieces],axis=1)
    lons=np.concatenate([part[2] for part in pieces])
    order=np.argsort(lons)
    lons=lons[order];vals=vals[:,order]
    # Remove duplicate columns at a split boundary, if present.
    _, keep=np.unique(np.round(lons,4),return_index=True)
    lons=lons[keep];vals=vals[:,keep]
    smoothed=gaussian_filter(vals,sigma=1.7)

    features=[]
    if field=='pressure':
        fig,ax=plt.subplots()
        cs=ax.contour(lons,lats,smoothed,levels=np.arange(900,1101,4))
        for level,segments in zip(cs.levels,cs.allsegs):
            for seg in segments:
                if len(seg)<3:continue
                # Grid-space smoothing keeps geographic positions intact.
                features.append({'type':'Feature','properties':{'hpa':int(level)},'geometry':{'type':'LineString','coordinates':np.round(seg,4).tolist()}})
        plt.close(fig)
    # North-up, with rgba so the underlying basemap remains legible.
    v=raster_to_mercator(smoothed[::-1,:],lats)
    ranges={'pressure':(970,1040),'cloud':(0,100),'temp':(-20,45),'humidity':(0,100),'rain':(0,12)}
    low,high=ranges[field];t=np.clip((v-low)/(high-low),0,1)
    stops={'pressure':['#424242','#999999','#f0f0f0'], 'cloud':['#101c30','#587aa0','#d7e9f5','#ffffff'], 'temp':['#3537a0','#008dd2','#32b58d','#f1d34e','#ee773a','#c32e49'], 'humidity':['#b7884a','#f4dc92','#8bc0bb','#2472a0'], 'rain':['#edf5ff','#6ba9e5','#1764c2','#6e3da2']}
    cmap=LinearSegmentedColormap.from_list(field,stops[field]);rgba=(cmap(t)*255).astype('uint8')
    rgba[:,:,3]=np.where(np.isfinite(v),155 if field!='cloud' else (t*190).astype('uint8'),0)
    if field=='cloud':rgba[:,:,3]=np.where(v<12,0,rgba[:,:,3])
    Image.fromarray(rgba,'RGBA').save(image_path)
    result={'field':field,'hour':fh,'cycle_utc':cycle.isoformat(),'valid_utc':(cycle+timedelta(hours=fh)).isoformat(),'bounds':[[float(lats[0]-(lats[1]-lats[0])/2),float(lons[0]-(lons[1]-lons[0])/2)],[float(lats[-1]+(lats[1]-lats[0])/2),float(lons[-1]+(lons[1]-lons[0])/2)]],'image':'/cache/'+image_path.name,'contours':{'type':'FeatureCollection','features':features},'min':round(float(np.nanmin(vals)),1),'max':round(float(np.nanmax(vals)),1),'shape':list(vals.shape),'source':'NOAA GFS 0.25°'}
    result_path.write_text(json.dumps(result,separators=(',',':')))
    return result

def get_frame(field,fh,lat,lon):
    if field not in FIELDS or fh not in (0,3,6,9,12,18,24,36,48):raise ValueError('Invalid field or forecast hour')
    bbox=area(lat,lon)
    errors=[]
    for cycle in cycle_candidates():
        try:return make_frame(field,fh,bbox,cycle)
        except Exception as e:errors.append(str(e)[:130])
    raise RuntimeError('NOAA grid unavailable: '+'; '.join(errors[:3]))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def do_GET(self):
        if urllib.parse.urlsplit(self.path).path=='/api/grid':
            try:
                p=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                field=p.get('field',['pressure'])[0];fh=int(p.get('hour',['0'])[0]);lat=float(p.get('lat',['-33.87'])[0]);lon=float(p.get('lon',['151.21'])[0])
                data=get_frame(field,fh,lat,lon);code=200
            except Exception as e:data={'error':str(e)};code=503
            body=json.dumps(data).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        elif urllib.parse.urlsplit(self.path).path.startswith('/cache/'):
            name=Path(urllib.parse.urlsplit(self.path).path).name
            if name.endswith('.png') and (CACHE/name).is_file():
                b=(CACHE/name).read_bytes()
                self.send_response(200)
                self.send_header('Content-Type','image/png')
                self.send_header('Content-Length',str(len(b)))
                self.end_headers();self.wfile.write(b)
            else:self.send_error(404)
        else:super().do_GET()

def make_server(port=0):
    return ThreadingHTTPServer(('127.0.0.1',int(port)),Handler)

if __name__=='__main__':
    server=make_server(8000)
    print('SkySynoptic development server at http://localhost:8000',flush=True)
    webbrowser.open('http://localhost:8000')
    server.serve_forever()

