"""Generate a small original SkySynoptic app icon, no third-party artwork."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math
N=1024
img=Image.new('RGBA',(N,N),(0,0,0,0))
d=ImageDraw.Draw(img)
d.rounded_rectangle((40,40,984,984),radius=205,fill=(32,33,35,255))
d.ellipse((165,185,859,879),outline=(147,151,156,255),width=15)
for j in (-2,-1,0,1,2):
    y=490+j*66
    points=[(160+i*6,y+int(26*math.sin(i/9.6+j*.55))) for i in range(118)]
    d.line(points,fill=(233,235,239,235) if j==0 else (165,172,181,150),width=18 if j==0 else 12,joint='curve')
d.ellipse((425,389,522,486),fill=(255,255,255,230))
img.save(Path(__file__).parent/'SkySynoptic-icon.png')
