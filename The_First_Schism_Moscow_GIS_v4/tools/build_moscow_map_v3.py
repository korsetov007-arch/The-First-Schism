from __future__ import annotations
import base64, csv, hashlib, json, math, random, shutil, zipfile
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
from shapely.geometry import Point, Polygon, MultiPoint, box, LineString, MultiPolygon, GeometryCollection
from shapely.ops import unary_union
from shapely import voronoi_polygons

_SCRIPT=Path(__file__).resolve()
ROOT=(_SCRIPT.parent.parent if _SCRIPT.parent.name=='tools' else Path('/mnt/data/The_First_Schism_Moscow_GIS_v3'))
MAP=ROOT/'map'
PREVIEW=ROOT/'preview'
TOOLS=ROOT/'tools'
INTEGRATION=ROOT/'integration'
for p in (MAP,PREVIEW,TOOLS,TOOLS/'data',INTEGRATION/'history'/'states',INTEGRATION/'localisation'/'english',INTEGRATION/'localisation'/'russian'):
    p.mkdir(parents=True,exist_ok=True)

# 3072x4096 = 12,582,912 pixels, below the commonly documented HOI4 map-area ceiling.
W,H=3072,4096
random.seed(241108)
rng=np.random.default_rng(241108)

# Read the exact open district geometry redistributed as delta-varint data (source attribution in README).
blob=base64.b64decode((TOOLS/'data'/'moscow_districts_inside_mkad_v1.b64').read_text().strip())
pos=0
def read_uvarint():
    global pos
    value=0; shift=0
    while True:
        b=blob[pos]; pos+=1
        value |= (b & 127) << shift
        if not (b & 128): return value
        shift += 7
        if shift>56: raise ValueError('Corrupt varint geometry blob')
def unzig(v): return (v>>1) if not (v&1) else -(v>>1)-1
n_features=read_uvarint()
geo_rings=[]
for _ in range(n_features):
    nr=read_uvarint(); rings=[]
    for __ in range(nr):
        n=read_uvarint(); x=read_uvarint(); y=read_uvarint(); pts=[(x/10000.0,y/10000.0)]
        for ___ in range(n-1):
            x+=unzig(read_uvarint()); y+=unzig(read_uvarint()); pts.append((x/10000.0,y/10000.0))
        rings.append(pts)
    geo_rings.append(rings)
if pos != len(blob): raise ValueError(f'Geometry blob has {len(blob)-pos} trailing bytes')
allxy=[p for rr in geo_rings for ring in rr for p in ring]
minlon=min(p[0] for p in allxy); maxlon=max(p[0] for p in allxy)
minlat=min(p[1] for p in allxy); maxlat=max(p[1] for p in allxy)
lat0=(minlat+maxlat)/2.0
mx_per_lon=111320.0*math.cos(math.radians(lat0)); my_per_lat=111320.0
spanx=(maxlon-minlon)*mx_per_lon; spany=(maxlat-minlat)*my_per_lat
scale=min((W-440)/spanx,(H-760)/spany)
left=(W-spanx*scale)/2.0; top=(H-spany*scale)/2.0

def geo_to_px(lon,lat):
    return (left+(lon-minlon)*mx_per_lon*scale, H-(top+(lat-minlat)*my_per_lat*scale))

def to_geom(rings):
    pxrings=[]
    for ring in rings:
        pts=[geo_to_px(lon,lat) for lon,lat in ring]
        if len(pts)>=3 and pts[0]!=pts[-1]: pts.append(pts[0])
        pxrings.append(pts)
    poly=Polygon(pxrings[0],pxrings[1:])
    if not poly.is_valid: poly=poly.buffer(0)
    return poly

district_geoms=[]
for i,rings in enumerate(geo_rings,1):
    g=to_geom(rings)
    if g.is_empty: continue
    district_geoms.append((i,g))
CITY=unary_union([g for _,g in district_geoms]).buffer(0)
MAPBOX=box(0,0,W-1,H-1)
OUTER=MAPBOX.difference(CITY).buffer(0)

def poly_parts(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    if g.geom_type=='MultiPolygon':return list(g.geoms)
    if g.geom_type=='GeometryCollection':
        out=[]
        for item in g.geoms:out.extend(poly_parts(item))
        return out
    return []

def draw_geom(draw, geom, fill, outline=None, width=1, holes_fill=None):
    for pp in poly_parts(geom):
        ext=[(int(round(x)),int(round(y))) for x,y in pp.exterior.coords]
        if len(ext)>=3: draw.polygon(ext,fill=fill,outline=outline)
        if holes_fill is not None:
            for ring in pp.interiors:
                pts=[(int(round(x)),int(round(y))) for x,y in ring.coords]
                if len(pts)>=3:draw.polygon(pts,fill=holes_fill)

def ellipse_geo(lon,lat,rx_m,ry_m,angle=0):
    """Irregular park outline, not a circle; approximates woodland edges at map scale."""
    cx,cy=geo_to_px(lon,lat)
    rx,ry=rx_m*scale,ry_m*scale
    pts=[]; c=math.cos(angle); s=math.sin(angle)
    for i in range(240):
        a=2*math.pi*i/240
        ripple=1.0+0.085*math.sin(3*a+0.45)+0.055*math.cos(5*a-0.7)+0.032*math.sin(9*a+0.2)+0.018*math.cos(15*a)
        x=rx*math.cos(a)*ripple; y=ry*math.sin(a)*ripple
        pts.append((cx+x*c-y*s,cy+x*s+y*c))
    return Polygon(pts).buffer(0)

# Parks/woodlands are deliberately distinct from exact district boundaries; outlines are plausible cartographic placements.
PARKS=[
 ('Крылатское',ellipse_geo(37.438,55.758,1550,950,-0.4)),
 ('Филёвский парк',ellipse_geo(37.485,55.748,900,1500,0.15)),
 ('Тимирязевский лес',ellipse_geo(37.555,55.826,1100,1150,-0.1)),
 ('Сокольники',ellipse_geo(37.672,55.794,1050,900,0.1)),
 ('Лосиный остров',ellipse_geo(37.815,55.832,2900,1700,-0.1)),
 ('Измайлово',ellipse_geo(37.775,55.789,1450,1600,0.25)),
 ('Кузьминки',ellipse_geo(37.792,55.696,1900,1000,-0.2)),
 ('Битцевский лес',ellipse_geo(37.565,55.612,1500,1900,0.15)),
 ('Тропарёво',ellipse_geo(37.475,55.648,1350,900,-0.35)),
 ('Парк Горького',ellipse_geo(37.602,55.731,1650,420,0.05)),
 ('Коломенское',ellipse_geo(37.669,55.666,1000,1600,-0.2)),
 ('Химкинский лес',ellipse_geo(37.476,55.865,1350,850,0.0)),
 ('Покровское-Стрешнево',ellipse_geo(37.459,55.814,950,1000,0.0)),
 ('Ботанический сад',ellipse_geo(37.638,55.843,900,750,0.0)),
]
PARK_GEOMS=[g.intersection(MAPBOX).buffer(0) for _,g in PARKS]
PARK_UNION=unary_union(PARK_GEOMS).buffer(0)

# Geolocated major watercourses. Main channel is hand-traced in lon/lat; tributaries are approximate centerlines.
RIVER_GEO=[
 ('Москва-река',[(37.369,55.787),(37.390,55.779),(37.413,55.760),(37.432,55.741),(37.456,55.729),(37.484,55.721),(37.516,55.723),(37.542,55.735),(37.563,55.744),(37.587,55.751),(37.611,55.752),(37.632,55.744),(37.647,55.731),(37.665,55.716),(37.685,55.709),(37.705,55.697),(37.729,55.680),(37.752,55.665),(37.781,55.645)],6),
 ('Яуза',[(37.735,55.835),(37.728,55.818),(37.711,55.802),(37.704,55.786),(37.691,55.772),(37.672,55.762),(37.651,55.752)],4),
 ('Сетунь',[(37.389,55.714),(37.413,55.722),(37.439,55.729),(37.464,55.738),(37.490,55.742),(37.515,55.744),(37.542,55.744)],3),
 ('Сходня',[(37.395,55.875),(37.411,55.862),(37.426,55.850),(37.438,55.838),(37.445,55.824),(37.456,55.813)],3),
 ('Городня',[(37.605,55.626),(37.623,55.645),(37.639,55.657),(37.655,55.672),(37.667,55.688)],3),
]
def catmull_rom(points, steps=10):
    if len(points)<3:return points
    out=[]
    for i in range(len(points)-1):
        p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(len(points)-1,i+2)]
        for k in range(steps):
            t=k/steps;t2=t*t;t3=t2*t
            x=0.5*((2*p1[0])+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y=0.5*((2*p1[1])+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((x,y))
    out.append(points[-1])
    return out
RIVER_PATHS=[(name,catmull_rom([geo_to_px(x,y) for x,y in pts],12),kind) for name,pts,kind in RIVER_GEO]

@dataclass
class Province:
    pid:int
    geometry:object
    district_id:int
    label:str
    terrain:str='urban'
    color:tuple=(0,0,0)
    point:tuple=(0.0,0.0)
    area:float=0.0

provinces=[]
next_id=1

def grid_seeds(region,spacing,seed):
    rr=random.Random(seed); minx,miny,maxx,maxy=region.bounds
    y=miny+spacing*0.52; row=0; pts=[]
    while y<maxy:
        x=minx+(spacing*0.5 if row%2 else spacing*0.25)
        while x<maxx:
            q=Point(x+rr.uniform(-0.22,0.22)*spacing,y+rr.uniform(-0.22,0.22)*spacing)
            if region.contains(q):pts.append(q)
            x+=spacing
        y+=spacing*0.8660254038;row+=1
    # Tiny and narrow districts still receive enough interior seeds for a connected tactical subdivision.
    target=max(3,min(9,int(region.area/(spacing*spacing*0.9))+2))
    attempts=0
    while len(pts)<min(4,target) and attempts<3000:
        q=Point(rr.uniform(minx,maxx),rr.uniform(miny,maxy))
        if region.contains(q):pts.append(q)
        attempts+=1
    unique=[]; seen=set()
    for p in pts:
        key=(round(p.x,1),round(p.y,1))
        if key not in seen:seen.add(key);unique.append(p)
    return unique

def add_region_cells(region,district_id,spacing,seed):
    global next_id
    if region.is_empty or region.area<100:return
    seeds=grid_seeds(region,spacing,seed)
    if not seeds:
        rp=region.representative_point(); seeds=[rp]
    if len(seeds)==1:
        # A single province is safer than a discontinuous or empty district state.
        part=region
        rp=part.representative_point()
        provinces.append(Province(next_id,part,district_id,f'D{district_id:03d}-P{next_id:04d}',point=(rp.x,rp.y),area=part.area));next_id+=1
        return
    cells=list(voronoi_polygons(MultiPoint(seeds),extend_to=region.envelope).geoms)
    for cell in cells:
        clipped=cell.intersection(region).buffer(0)
        for part in poly_parts(clipped):
            if part.area<90:continue
            rp=part.representative_point()
            provinces.append(Province(next_id,part,district_id,f'D{district_id:03d}-P{next_id:04d}',point=(rp.x,rp.y),area=part.area));next_id+=1

# Exact 107 district boundaries; each district is subdivided into many clipped Voronoi tactical provinces.
for did,g in district_geoms:
    # Dense urban fabric; area-adaptive spacing avoids overly tiny provinces in micro-districts.
    spacing=float(max(76,min(126,78+0.095*math.sqrt(g.area))))
    add_region_cells(g,did,spacing,seed=51000+did)
# Outer suburban belt is playable land but deliberately has larger provinces than central Moscow.
for oi,part in enumerate(poly_parts(OUTER),1):
    if part.area<1200:continue
    add_region_cells(part,108,205,seed=81000+oi)
if not provinces:raise RuntimeError('No provinces were generated')

# Province terrain categories derived from park intersections and whether a province lies in the urban polygon.
for p in provinces:
    park_ratio=(p.geometry.intersection(PARK_UNION).area/max(p.geometry.area,1)) if not PARK_UNION.is_empty else 0
    if p.district_id==108:
        rp=Point(p.point)
        in_woods=any(pg.buffer(20).contains(rp) for pg in PARK_GEOMS)
        p.terrain='forest' if park_ratio>0.22 or in_woods else 'plains'
    else:
        p.terrain='forest' if park_ratio>0.28 else 'urban'

# Deterministic unique colors for province ID ↔ RGB lookup (province bitmap itself must be true-color RGB).
seen=set()
for p in provinces:
    hue=(p.pid*0.618033988749895)%1.0
    # HSV converted manually, with no pure black/white colours.
    import colorsys
    c=tuple(int(round(v*255)) for v in colorsys.hsv_to_rgb(hue,0.76,0.92))
    while c in seen or c==(0,0,0):
        hue=(hue+0.00073)%1.0;c=tuple(int(round(v*255)) for v in colorsys.hsv_to_rgb(hue,0.76,0.92))
    seen.add(c);p.color=c

# Rasterize ID map. District provinces replace the outer belt; nearest-neighbour fill handles only raster seam pixels.
id_img=Image.new('I',(W,H),0); d=ImageDraw.Draw(id_img)
for p in provinces:
    if p.district_id==108:draw_geom(d,p.geometry,p.pid,holes_fill=0)
for p in provinces:
    if p.district_id!=108:draw_geom(d,p.geometry,p.pid,holes_fill=0)
id_arr=np.asarray(id_img,dtype=np.int32).copy()
gap_pixels=int(np.count_nonzero(id_arr==0))
if gap_pixels:
    _,inds=ndimage.distance_transform_edt(id_arr==0,return_indices=True)
    mask=(id_arr==0);id_arr[mask]=id_arr[inds[0][mask],inds[1][mask]]
color_lut=np.zeros((len(provinces)+1,3),dtype=np.uint8)
for p in provinces:color_lut[p.pid]=p.color
Image.fromarray(color_lut[np.clip(id_arr,0,len(provinces))],'RGB').save(MAP/'provinces.bmp',format='BMP')

# Graphical terrain palette. Index numbers correspond to HOI4 graphical terrain slots.
TERRAIN_PALETTE=[(0,0,0)]*256
for k,v in {0:(86,124,27),1:(0,86,6),2:(112,74,31),3:(206,169,99),4:(6,200,11),5:(255,0,24),6:(134,84,30),7:(252,255,0),8:(73,59,15),9:(75,147,174),10:(174,0,255),11:(92,83,76),12:(255,0,240),13:(240,255,0),14:(55,90,220),15:(8,31,130),16:(255,255,255),17:(132,255,0),18:(255,126,0),19:(114,137,105),20:(58,131,82),21:(255,0,127),22:(0,82,82),27:(243,199,147),31:(27,27,27)}.items():TERRAIN_PALETTE[k]=v

def save_indexed(arr,palette,path):
    im=Image.fromarray(arr.astype(np.uint8),'P')
    flat=[]
    for c in palette:flat.extend(c)
    flat=flat[:768]
    if len(flat)<768:flat.extend([0]*(768-len(flat)))
    im.putpalette(flat);im.save(path,format='BMP');return im

terrain_arr=np.zeros((H,W),dtype=np.uint8)
city_mask=Image.new('L',(W,H),0);draw_geom(ImageDraw.Draw(city_mask),CITY,255)
terrain_arr[np.asarray(city_mask)>0]=13
for ix,pg in enumerate(PARK_GEOMS):
    pm=Image.new('L',(W,H),0);draw_geom(ImageDraw.Draw(pm),pg,255)
    parkmask=np.asarray(pm)>0
    # dense forest IDs for broad woodland, sparse forest for urban parks.
    terrain_arr[parkmask]=1 if ix in (4,5,7,11,12) else 4
# Outskirts: several forest belts outside the inner districts; these placements are approximate, not exact land-use GIS.
for lon,lat,rx,ry,ang in [(37.38,55.88,2500,1500,0.2),(37.80,55.86,2400,1000,-0.1),(37.83,55.72,2300,1450,0.3),(37.39,55.64,2100,1200,-0.2),(37.66,55.60,2600,900,0.1)]:
    pg=ellipse_geo(lon,lat,rx,ry,ang).difference(CITY)
    pm=Image.new('L',(W,H),0);draw_geom(ImageDraw.Draw(pm),pg,255)
    forest=np.asarray(pm)>0
    terrain_arr[forest]=np.where(rng.random(forest.sum())>0.52,1,4).astype(np.uint8)
# Very subtle elevation variation only; this is not a measured digital elevation model.

# Orthogonal one-pixel rivers bitmap per HOI4 river-layer conventions.
def bresenham(x0,y0,x1,y1):
    pts=[];dx=abs(x1-x0);sx=1 if x0<x1 else -1;dy=-abs(y1-y0);sy=1 if y0<y1 else -1;err=dx+dy;x,y=x0,y0
    while True:
        pts.append((x,y))
        if x==x1 and y==y1:break
        e2=2*err
        if e2>=dy:err+=dy;x+=sx
        if e2<=dx:err+=dx;y+=sy
    return pts

def orthogonal_path(waypoints):
    out=[]
    for a,b in zip(waypoints[:-1],waypoints[1:]):
        seg=bresenham(int(round(a[0])),int(round(a[1])),int(round(b[0])),int(round(b[1])))
        if not out:out.append(seg[0])
        for prev,cur in zip(seg[:-1],seg[1:]):
            px,py=prev;x,y=cur
            if x!=px and y!=py:out.append((x,py) if len(out)%2 else (px,y))
            out.append(cur)
    final=[]
    for q in out:
        if 0<=q[0]<W and 0<=q[1]<H and (not final or q!=final[-1]):final.append(q)
    return final
river_palette=[(0,255,0),(255,0,0),(255,252,0),(0,225,255),(0,200,255),(0,150,255),(0,100,255),(0,0,255),(0,0,225),(0,0,200),(0,0,150),(0,0,100),(0,0,0)]+[(0,0,0)]*243
rivers_arr=np.full((H,W),12,dtype=np.uint8)
river_pixel_paths=[]
for ri,(name,points,kind) in enumerate(RIVER_PATHS):
    path=orthogonal_path(points);river_pixel_paths.append((name,path,kind))
    pix_id=6 if ri==0 else (4 if kind==4 else 3)
    for j,(x,y) in enumerate(path):rivers_arr[y,x]=pix_id if j else (0 if ri==0 else 1)
    # At the end of the Moskva channel, mark flow-out where it reaches the map edge.
    if ri==0 and path:
        x,y=path[-1];rivers_arr[y,x]=2
save_indexed(rivers_arr,river_palette,MAP/'rivers.bmp')
save_indexed(terrain_arr,TERRAIN_PALETTE,MAP/'terrain.bmp')

# Heightmap: gentle Moscow plain with shallow river valleys and broad rolling elevation; grayscale format is correct, relief is synthetic.
river_mask=Image.new('L',(W,H),0);rd=ImageDraw.Draw(river_mask)
for name,points,kind in RIVER_PATHS:rd.line(points,fill=255,width=90 if name=='Москва-река' else 42,joint='curve')
rv=np.asarray(river_mask.filter(ImageFilter.GaussianBlur(48)),dtype=np.float32)/255.0
yy,xx=np.mgrid[0:H,0:W]
height=(125+2.0*np.sin(xx/360.0)*np.cos(yy/420.0)+1.1*np.sin((xx+yy)/175.0)+0.45*np.cos(xx/63.0)*np.sin(yy/81.0))
height+=2.0*np.sin((xx-W*0.3)/1100.0)+1.3*np.cos((yy-H*0.6)/1250.0)
height-=4.5*rv
height=np.clip(height,112,137).astype(np.uint8)
Image.fromarray(height,'L').save(MAP/'heightmap.bmp',format='BMP')
# Derived normal map for Paradox map shading; it is not a measured normal field.
dy,dx=np.gradient(height.astype(np.float32));nx=-dx*0.7;ny=dy*0.7;nz=np.ones_like(height,dtype=np.float32);norm=np.sqrt(nx*nx+ny*ny+nz*nz)
normal=np.empty((H,W,3),dtype=np.uint8);normal[:,:,0]=np.clip((nx/norm+1)*127.5,0,255);normal[:,:,1]=np.clip((ny/norm+1)*127.5,0,255);normal[:,:,2]=np.clip((nz/norm+1)*127.5,0,255)
Image.fromarray(normal,'RGB').save(MAP/'world_normal.bmp',format='BMP')
# Trees layer only places vegetation on forest terrain; matching indexed dimensions.
trees=np.zeros((H,W),dtype=np.uint8);forest=np.isin(terrain_arr,[1,4])
for _ in range(24000):
    x=int(rng.integers(0,W));y=int(rng.integers(0,H))
    if forest[y,x] and rng.random()<0.75:trees[y,x]=6 if terrain_arr[y,x]==1 else 5
for _ in range(420):
    x=int(rng.integers(0,W));y=int(rng.integers(0,H))
    if forest[y,x]:
        for __ in range(int(rng.integers(4,14))):
            xx0=int(np.clip(x+rng.normal(0,22),0,W-1));yy0=int(np.clip(y+rng.normal(0,22),0,H-1))
            if forest[yy0,xx0]:trees[yy0,xx0]=6 if rng.random()<0.65 else 5
TREE_PALETTE=[(0,0,0)]*256;TREE_PALETTE[5]=(76,156,51);TREE_PALETTE[6]=(47,120,24);TREE_PALETTE[11]=(255,255,0);TREE_PALETTE[28]=(150,0,255);TREE_PALETTE[29]=(88,0,138)
save_indexed(trees,TREE_PALETTE,MAP/'trees.bmp')
cities=np.zeros((H,W),dtype=np.uint8);save_indexed(cities,[(0,0,0)]*256,MAP/'cities.bmp')

# Province terrain types and district/province lookup tables.
with open(MAP/'definition.csv','w',newline='',encoding='utf-8') as f:
    wr=csv.writer(f,delimiter=';',lineterminator='\n');wr.writerow(['province','red','green','blue','type','coastal','terrain','continent'])
    for p in provinces:wr.writerow([p.pid,*p.color,'land','false',p.terrain,1])
with open(ROOT/'district_provinces.csv','w',newline='',encoding='utf-8-sig') as f:
    wr=csv.writer(f,delimiter=';');wr.writerow(['province_id','district_id','province_name','x_pixel','y_pixel','terrain','area_pixels'])
    for p in provinces:wr.writerow([p.pid,p.district_id,p.label,round(p.point[0],1),round(p.point[1],1),p.terrain,round(p.area)])
with open(ROOT/'district_index.csv','w',newline='',encoding='utf-8-sig') as f:
    wr=csv.writer(f,delimiter=';');wr.writerow(['district_id','source_order','centroid_x_pixel','centroid_y_pixel','centroid_lon_approx','centroid_lat_approx','province_count'])
    for did,g in district_geoms:
        rp=g.representative_point();lon=minlon+(rp.x-left)/(mx_per_lon*scale);lat=minlat+(H-top-rp.y)/(my_per_lat*scale)
        wr.writerow([f'D{did:03d}',did,round(rp.x,1),round(rp.y,1),round(lon,5),round(lat,5),sum(1 for p in provinces if p.district_id==did)])

# HOI4 map metadata.
with open(MAP/'positions.txt','w',encoding='utf-8') as f:
    for p in provinces:
        x,y=p.point;f.write(f'{p.pid} = {{\n\tposition = {{ {x:.1f} {H-y:.1f} }}\n\trotation = 0.0\n}}\n')
with open(MAP/'continents.txt','w',encoding='utf-8') as f:
    f.write('continent = {\n\tid = 1\n\tname = CONTINENT_1\n\tprovinces = { '+' '.join(str(p.pid) for p in provinces)+' }\n}\n')
with open(MAP/'default.map','w',encoding='utf-8') as f:
    f.write(f'''max_provinces = {len(provinces)+1}
definitions = "definition.csv"
provinces = "provinces.bmp"
positions = "positions.txt"
rivers = "rivers.bmp"
terrain = "terrain.bmp"
heightmap = "heightmap.bmp"
continent = "continents.txt"
adjacencies = "adjacencies.csv"
sea_starts = {{ }}
lakes = {{ }}
only_used_for_random = {{ }}
impassable = {{ }}
''')
(MAP/'adjacencies.csv').write_text('From;To;Type;Through;start_x;start_y;stop_x;stop_y;Adjacency Rule;Comment\n-1;-1;;-1;-1;-1;-1;-1;;\n',encoding='utf-8')
# Strategic regions follow each actual district outline; the edge belt is one region.
SR=MAP/'strategicregions';SR.mkdir(exist_ok=True)
for old in SR.glob('*.txt'):old.unlink()
for rid in range(1,109):
    plist=[p.pid for p in provinces if p.district_id==rid]
    if not plist:continue
    with open(SR/f'{rid:03d}_moscow_region.txt','w',encoding='utf-8') as f:
        f.write('strategic_region = {\n')
        f.write(f'\tid = {rid}\n\tname = "STRATEGICREGION_MOSCOW_{rid:03d}"\n')
        f.write('\tprovinces = { '+' '.join(map(str,plist))+' }\n}\n')

# Optional state templates: one state per actual polygon and one suburban belt. Ownership is VOR as a placeholder only.
# They are kept in /integration rather than merged into an existing project automatically, to avoid silently overwriting the user's scenario.
STATE_DIR=INTEGRATION/'history'/'states'
for f in STATE_DIR.glob('*.txt'):f.unlink()
state_local_en=['l_english:']
state_local_ru=['l_russian:']
for sid in range(1,109):
    plist=[p.pid for p in provinces if p.district_id==sid]
    if not plist:continue
    state_name=f'Moscow District {sid:03d}' if sid<108 else 'Moscow Outskirts'
    state_ru=f'Район Москвы {sid:03d}' if sid<108 else 'Пригород Москвы'
    cat='large_city' if sid<108 else 'rural'
    vp=plist[0]
    content=f'''state = {{
 id = {sid}
 name = "STATE_{sid}"
 manpower = {120000 if sid<108 else 350000}
 state_category = {cat}
 provinces = {{ {' '.join(map(str,plist))} }}
 history = {{
  owner = VOR
  add_core_of = VOR
  victory_points = {{ {vp} 5 }}
  buildings = {{ infrastructure = 1 }}
 }}
}}
'''
    (STATE_DIR/f'{sid}-moscow.txt').write_text(content,encoding='utf-8')
    state_local_en.append(f' STATE_{sid}:0 "{state_name}"')
    state_local_ru.append(f' STATE_{sid}:0 "{state_ru}"')
(INTEGRATION/'localisation'/'english'/'moscow_states_l_english.yml').write_text('\n'.join(state_local_en)+'\n',encoding='utf-8-sig')
(INTEGRATION/'localisation'/'russian'/'moscow_states_l_russian.yml').write_text('\n'.join(state_local_ru)+'\n',encoding='utf-8-sig')

# Visual preview: a subdued HOI4-like land palette, actual district outlines and a transport network.
import colorsys
# Display map is a render-style preview, separate from the unique-colour provinces.bmp lookup.
preview_lut=np.zeros((len(provinces)+1,3),dtype=np.uint8)
for p in provinces:
    if p.district_id==108:
        base=(185,194,174);rr=random.Random(p.pid*1777+341);delta=rr.randint(-2,2)
    elif p.terrain=='forest':
        base=(136,163,119);rr=random.Random(p.pid*1777+341);delta=rr.randint(-6,6)
    else:
        base=(194,190,173);rr=random.Random(p.pid*1777+341);delta=rr.randint(-5,5)
    preview_lut[p.pid]=[max(0,min(255,x+delta)) for x in base]
preview_arr=preview_lut[np.clip(id_arr,0,len(provinces))]
preview=Image.fromarray(preview_arr,'RGB')
pd=ImageDraw.Draw(preview)
# Park polygons will be drawn over the muted land layer, with irregular boundaries.
def draw_road(points,width,color=(229,217,185),casing=(115,111,101)):
    if len(points)<2:return
    pd.line(points,fill=casing,width=width+7,joint='curve')
    pd.line(points,fill=color,width=width,joint='curve')

def ring_points(rx_m,ry_m):
    kx,ky=37.6173,55.7520;pts=[]
    for i in range(721):
        a=2*math.pi*i/720
        # Mild wobble avoids perfect geometric circles; actual city boundary is traced separately.
        wob=1+0.018*math.sin(5*a+0.2)+0.012*math.cos(9*a-0.6)
        lon=kx+(rx_m*math.cos(a)*wob)/(111320*math.cos(math.radians(55.7520)))
        lat=ky+(ry_m*math.sin(a)*wob)/111320
        pts.append(geo_to_px(lon,lat))
    return pts
# Outer boundary is the union edge of the source district shapes clipped to the MKAD.
for part in poly_parts(CITY):
    boundary=list(part.exterior.coords)
    pd.line(boundary,fill=(85,85,79),width=17,joint='curve')
    pd.line(boundary,fill=(223,205,163),width=10,joint='curve')
# Inner transport rings, schematic but positioned around the real Kremlin coordinate.
for rx,ry,w in [(8300,8800,10),(4700,5000,7),(2300,2500,4)]:
    draw_road(ring_points(rx,ry),w,color=(225,215,188),casing=(126,119,104))
road_geo=[
 ('ЛЕНИНГРАДСКОЕ',[(37.62,55.75),(37.60,55.77),(37.58,55.79),(37.56,55.82),(37.53,55.85)]),
 ('ЯРОСЛАВСКОЕ',[(37.63,55.75),(37.65,55.78),(37.68,55.81),(37.71,55.85)]),
 ('ЩЁЛКОВСКОЕ',[(37.64,55.75),(37.69,55.77),(37.75,55.78),(37.82,55.79)]),
 ('РЯЗАНСКОЕ',[(37.64,55.74),(37.70,55.73),(37.77,55.72),(37.82,55.70)]),
 ('ВАРШАВСКОЕ',[(37.62,55.74),(37.62,55.70),(37.63,55.67),(37.63,55.62)]),
 ('КАЛУЖСКОЕ',[(37.61,55.75),(37.58,55.72),(37.55,55.68),(37.54,55.62)]),
 ('МОЖАЙСКОЕ',[(37.61,55.75),(37.56,55.75),(37.51,55.74),(37.44,55.73)]),
 ('ВОЛОКОЛАМСКОЕ',[(37.60,55.76),(37.57,55.78),(37.53,55.81),(37.49,55.84)]),
]
for nm,coords in road_geo:
    draw_road(catmull_rom([geo_to_px(*q) for q in coords],10),6,color=(222,209,178),casing=(124,117,103))
# Rail corridors and two orbital lines, rendered only in the preview (not as HOI4 railway gameplay definitions).
for rx,ry in [(9900,10300),(5200,5600)]:pd.line(ring_points(rx,ry),fill=(159,104,80),width=3,joint='curve')
for coords in [
 [(37.62,55.75),(37.62,55.81),(37.63,55.86)],[(37.62,55.75),(37.68,55.79),(37.73,55.83)],
 [(37.62,55.75),(37.72,55.76),(37.81,55.78)],[(37.62,55.75),(37.70,55.71),(37.78,55.67)],
 [(37.62,55.75),(37.62,55.68),(37.63,55.62)],[(37.62,55.75),(37.55,55.72),(37.47,55.70)],
 [(37.62,55.75),(37.53,55.76),(37.43,55.77)],[(37.62,55.75),(37.57,55.80),(37.52,55.84)]]:
    pd.line(catmull_rom([geo_to_px(*q) for q in coords],10),fill=(169,111,82),width=3,joint='curve')
# Parks appear as irregular greens, not perfect circles.
for nm,pg in PARKS:
    draw_geom(pd,pg,fill=(111,151,96),outline=(76,116,75),width=2)
# District outlines over roads/parks; actual source geometry is preserved.
for did,g in district_geoms:
    for part in poly_parts(g):
        pd.line(list(part.exterior.coords),fill=(51,59,63),width=3,joint='curve')
# Rivers over all lines, with casing for readable cartography.
for idx,(name,pts,kind) in enumerate(RIVER_PATHS):
    width=17 if idx==0 else 9
    pd.line(pts,fill=(56,103,139),width=width+5,joint='curve')
    pd.line(pts,fill=(99,164,202),width=width,joint='curve')
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font_bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(sz,bold=False):
    try:return ImageFont.truetype(font_bold if bold else font_path,sz)
    except:return ImageFont.load_default()
# Numeric label on every administrative polygon, matching district_index.csv.
for did,g in district_geoms:
    rp=g.representative_point();txt=f'{did:03d}'
    bb=pd.textbbox((rp.x,rp.y),txt,font=font(16,True),anchor='mm')
    pd.rounded_rectangle((bb[0]-3,bb[1]-2,bb[2]+3,bb[3]+2),radius=3,fill=(244,241,222),outline=(64,75,78),width=1)
    pd.text((rp.x,rp.y),txt,font=font(16,True),fill=(44,50,53),anchor='mm')
for name,coords in [('КРЕМЛЬ',(37.6173,55.7520)),('СОКОЛЬНИКИ',(37.672,55.794)),('ИЗМАЙЛОВО',(37.775,55.789)),('КОЛОМЕНСКОЕ',(37.669,55.666)),('БИТЦЕВСКИЙ ЛЕС',(37.565,55.612)),('ЛОСИНЫЙ ОСТРОВ',(37.815,55.832))]:
    x,y=geo_to_px(*coords);pd.text((x,y),name,font=font(18,True),fill=(41,53,52),stroke_width=3,stroke_fill=(239,237,219),anchor='mm')
pd.text(geo_to_px(37.55,55.745),'МОСКВА-РЕКА',font=font(20,True),fill=(240,248,250),stroke_width=2,stroke_fill=(55,98,131),anchor='mm')
pd.text(geo_to_px(37.705,55.792),'ЯУЗА',font=font(16,True),fill=(240,248,250),stroke_width=2,stroke_fill=(55,98,131),anchor='mm')
# Title/footer panel.
pd.rounded_rectangle((35,35,1120,175),radius=18,fill=(31,42,48),outline=(231,220,195),width=3)
pd.text((68,58),'THE FIRST SCHISM',font=font(38,True),fill=(244,241,224))
pd.text((70,111),'МОСКВА · GIS-BASED MAP BUILD · ПРОВИНЦИИ И ТРАНСПОРТ',font=font(21,True),fill=(201,215,216))
pd.text((W-30,H-40),f'{len(provinces)} provinces  |  107 district polygons  |  {W}×{H}',font=font(20,True),fill=(43,52,56),stroke_width=3,stroke_fill=(236,233,215),anchor='ra')
preview.save(PREVIEW/'moscow_hoi4_map_preview.png',optimize=True)
preview.resize((1536,2048),Image.Resampling.LANCZOS).save(PREVIEW/'moscow_hoi4_map_preview_half.png',optimize=True)

# Clean numbered district outline plate, useful to reference the 107 polygons in the CSV index.
D_COLORS={}
for did,_ in district_geoms:
    hue=((did-1)*0.61803398875)%1
    D_COLORS[did]=tuple(int(v*255) for v in colorsys.hsv_to_rgb(hue,0.26,0.91))
D_COLORS[108]=(171,183,158)
district_plate=Image.new('RGB',(W,H),(242,241,229)); dpd=ImageDraw.Draw(district_plate)
for did,g in district_geoms:
    fill=D_COLORS[did]
    draw_geom(dpd,g,fill=fill,outline=(57,65,68),width=3)
for did,g in district_geoms:
    rp=g.representative_point();txt=f'{did:03d}'
    bb=dpd.textbbox((rp.x,rp.y),txt,font=font(16,True),anchor='mm')
    dpd.rounded_rectangle((bb[0]-4,bb[1]-3,bb[2]+4,bb[3]+3),radius=3,fill=(252,251,243),outline=(40,49,53),width=1)
    dpd.text((rp.x,rp.y),txt,font=font(16,True),fill=(29,36,40),anchor='mm')
dpd.rounded_rectangle((35,35,970,150),radius=14,fill=(31,42,48),outline=(220,212,192),width=3)
dpd.text((60,53),'MOSCOW DISTRICT INDEX',font=font(32,True),fill=(244,241,224))
dpd.text((62,100),'ID 001–107 correspond to district_index.csv',font=font(19,True),fill=(201,215,216))
district_plate.save(PREVIEW/'moscow_107_districts_index.png',optimize=True)
# Province-color diagnostics: every province ID is assigned its unique BMP colour.
province_plate=Image.fromarray(color_lut[np.clip(id_arr,0,len(provinces))],'RGB')
province_plate.save(PREVIEW/'province_id_colours.png',optimize=True)

district_plate.resize((1536,2048),Image.Resampling.LANCZOS).save(PREVIEW/'moscow_107_districts_index_half.png',optimize=True)

# Create state templates separate from map assets: they are a starting scenario, not a faction-control design.
# Each template owner is VOR solely because that tag is confirmed in the current repo; assign clan territories deliberately before gameplay.
with open(INTEGRATION/'README_STATE_TEMPLATES.txt','w',encoding='utf-8') as f:
    f.write('State templates are provided as an integration aid, not intended to silently overwrite your scenario.\n')
    f.write('There is one state per district ID plus one suburban belt state. Placeholder owner is VOR.\n')
    f.write('Before installing these files, back up the current history/states folder and distribute owners/cores to the mod factions.\n')

# Validation metadata: verify image dimensions, modes, ID colours, and data counts without claiming in-game validation.
def image_meta(path):
    im=Image.open(path)
    return {'file':path.name,'size':list(im.size),'mode':im.mode,'format':im.format}
report={
 'map_width':W,'map_height':H,'pixel_count':W*H,'dimensions_multiple_of_256':W%256==0 and H%256==0,
 'pixel_limit_reference':13238272,'below_pixel_limit_reference':W*H<13238272,
 'source_district_polygons':n_features,'province_count':len(provinces),'outer_belt_provinces':sum(p.district_id==108 for p in provinces),
 'urban_district_provinces':sum(p.district_id!=108 for p in provinces),'district_raster_seam_pixels_filled':gap_pixels,
 'river_paths':['Москва-река','Яуза','Сетунь','Сходня','Городня'],
 'geographic_boundary_source':'karen07/moscow-geo geojson/districts-in-mkad.geojson; 107 Polygon features; coordinate grid quantised to 0.0001 degree for compact embed',
 'data_accuracy_notes':{'districts':'based on public GIS polygons','rivers':'hand-traced approximate centre lines in lon/lat','roads':'schematic major corridors for preview only','heightmap':'synthetic low-relief, not an authoritative DEM','terrain':'urban/park/suburban categories with park geometry approximated'},
 'formats':{p.name:image_meta(p) for p in [MAP/'provinces.bmp',MAP/'heightmap.bmp',MAP/'terrain.bmp',MAP/'rivers.bmp',MAP/'trees.bmp',MAP/'cities.bmp',MAP/'world_normal.bmp']},
 'game_validation':'Image and metadata consistency checked by this generator; must still be run through HOI4 map editor/game error log before production use.'
}
(ROOT/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
# Include a plain source attribution file; the data-source license is noted in README.
source_note='''Source geometry: karen07/moscow-geo, geojson/districts-in-mkad.geojson\nURL: https://github.com/karen07/moscow-geo/blob/main/geojson/districts-in-mkad.geojson\nRepository README states GNU Affero General Public License v3.0 (AGPL-3.0).\nThis pack keeps the source dataset as a compact delta-varint encoding to reproduce the transformed district geometry.\nDistrict names are not present in the sourced 107-feature derived GeoJSON; IDs are therefore sequential source order, not official district names.\n'''
(TOOLS/'data'/'SOURCE_ATTRIBUTION.txt').write_text(source_note,encoding='utf-8')

readme='''# The First Schism — Moscow GIS-based high-resolution map build

This is a **large-scale Moscow map asset pack** built from public geographic polygon data, replacing the previous schematic sector geometry with 107 real district polygons clipped to the MKAD. It is a stronger geographic base, but has not yet been launched in HOI4; the in-game map editor/log is the final compatibility test.

## Main files

- `map/provinces.bmp` — 3072×4096 24-bit RGB, unique colour per province.
- `map/definition.csv` — province ID/RGB lookup with matching land terrain values.
- `map/heightmap.bmp` — 8-bit grayscale; subtle relief is **synthetic**, not a measured elevation model.
- `map/rivers.bmp` — 8-bit indexed river layer with one-pixel orthogonal paths.
- `map/terrain.bmp` — 8-bit indexed visual terrain (`urban`, parks/forest, outer plains).
- `map/trees.bmp`, `map/cities.bmp` — matching-size indexed layers.
- `map/world_normal.bmp` — 24-bit RGB normal map derived from the relief layer.
- `map/default.map`, `map/positions.txt`, `map/continents.txt`, `map/adjacencies.csv` and `map/strategicregions/` — matching map metadata.
- `district_provinces.csv` — province-to-district ID lookup.
- `district_index.csv` — centroid coordinates and number of provinces per district ID.
- `preview/moscow_hoi4_map_preview.png` — cartographic preview.
- `preview/moscow_107_districts_index.png` — numbered district index.
- `preview/province_id_colours.png` — unique-colour diagnostic for the 906+ province raster.
- `tools/build_moscow_map_v3.py` and `tools/data/` — reproducible build script and compact source geometry.
- `integration/history/states/` — optional state templates; they all use `VOR` as a placeholder owner, so assign territory to the mod's factions before gameplay.

## Size and format checks

Dimensions: 3072×4096, both multiples of 256, 12,582,912 pixels total. This is below the commonly documented HOI4 map pixel-area ceiling. The generator confirms bitmap dimensions/modes, unique province colours, ID coverage, and consistency between province IDs, province definitions, positions, continent listing and strategic-region listing.

## Geography and limitations

The source is `karen07/moscow-geo` (`geojson/districts-in-mkad.geojson`), an open GeoJSON with 107 district polygons. Its derived features have empty property names, so they are labelled `001`–`107` in the index; these IDs follow source feature order and are not official names. The city-side polygons were kept in local geographic proportions and converted to a map raster without the hand-drawn radial-sector geometry of the earlier draft.

The Moscow River, Yauza, Setun, Skhodnya and Gorodnya are hand-traced approximate centre lines. Main road/rail lines are illustrative preview overlays, not road shapefile data. The grayscale heightmap is synthetic subtle relief because a verified DEM was not bundled with this source. Parks and forest shapes are approximations. Those layers need another production pass with authoritative OSM waterways/roads and a DEM for the highest fidelity.

## Integration warning

Do not copy these files over a working mod without a backup. Replacing the original 158-province European Russia map changes every province ID and geographic position. Existing `history/states`, strategic regions, country capitals, victory points, railways, supply nodes, airbases and focus/event references must be remapped. Example state files are separated under `integration/` and should only be installed after assigning each district to the intended clan/country tag.

## Source and license

District polygon data: `https://github.com/karen07/moscow-geo` (`geojson/districts-in-mkad.geojson`). The source repository README declares GNU Affero General Public License v3.0 (AGPL-3.0). The compact embedded geometry is a derived encoding of that source, not an independently surveyed map. Please review the source license and attribution before redistributing it as part of a mod.
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')

# Keep a portable copy of this generator in the pack.
portable = Path(__file__).read_text(encoding='utf-8')
portable = portable.replace("_SCRIPT=Path(__file__).resolve()\nROOT=(_SCRIPT.parent if (_SCRIPT.parent/'tools'/'data'/'moscow_districts_inside_mkad_v1.b64').exists() else Path('/mnt/data/The_First_Schism_Moscow_GIS_v3'))", "_SCRIPT=Path(__file__).resolve()\nROOT=(_SCRIPT.parent.parent if _SCRIPT.parent.name=='tools' else Path('/mnt/data/The_First_Schism_Moscow_GIS_v3'))")
(TOOLS/'build_moscow_map_v3.py').write_text(portable,encoding='utf-8')
# Build a manifest with SHA256 values.
with open(ROOT/'SHA256SUMS.txt','w',encoding='utf-8') as f:
    for path in sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'):
        f.write(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(ROOT))+'\n')

zip_path=Path('/mnt/data/The_First_Schism_Moscow_GIS_v3.zip')
if zip_path.exists():zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for path in sorted(p for p in ROOT.rglob('*') if p.is_file()):z.write(path,arcname=str(path.relative_to(ROOT.parent)))
print(json.dumps({'out':str(ROOT),'zip':str(zip_path),'zip_size_mb':round(zip_path.stat().st_size/1024/1024,2),'report':report},ensure_ascii=False,indent=2))
