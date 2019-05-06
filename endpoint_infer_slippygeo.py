from tqdm import tqdm
import pandas as pd
import numpy as np
from shapely import geometry
import geopandas as gpd
import glob,os
import sagemaker
import json
import argparse

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
  lat_deg = np.degrees(lat_rad)
  return (lat_deg, lon_deg)
  

parser = argparse.ArgumentParser()
parser.add_argument('-mod', '--endpointName', dest='endpointName')
parser.add_argument('-a', '--attribute', dest='attribute')
parser.add_argument('-c', '--classes', nargs='+', dest='classes')
parser.add_argument('-r', '--rec_prefix', dest='rec_prefix')
parser.add_argument('-t', '--thresh', dest='thresh',help='detection threshold confidence')
parser.add_argument('-ro', '--role', dest='role',help='s3 role')
parser.add_argument('-pa', '--path', dest='path',help='local path to tms files')
parser.add_argument('-z', '--zoom', dest='zoom',help='zoom level TMS', default='18')
args = parser.parse_args()

sagemaker_session = sagemaker.Session()
role              = args.role
endpointName      = args.endpointName 
predictor = sagemaker.predictor.RealTimePredictor(endpointName, 
               sagemaker_session=sagemaker_session,content_type='image/png')

print('sagemaker endpoint is: ',endpointName)

object_categories = args.classes 

files=glob.glob(args.path+args.zoom+'/*/*png')


xlist,ylist,zlist,geomlist,filelist,klasslist,scorelist=[],[],[],[],[],[],[]
for j in tqdm(files):
	file_name = j 
	with open(j, 'rb') as image:
		f = image.read()
		b = bytearray(f)
		ne = open('n.txt','wb')
		ne.write(b)
	results = predictor.predict(b)
	detections = json.loads(results)
	df=pd.DataFrame(detections['prediction'],columns=['klass', 'score', 'x0', 'y0','x1', 'y1'])
	df['geometry']=''
	zoom,x,y=j.split('/')[-3],j.split('/')[-2],j.split('/')[-1].split('.')[0]
	for i in range(0,len(df)):
		filelist.append(j.split('/')[-3]+'_'+j.split('/')[-2]+'_'+j.split('/')[-1].split('.')[0])
		zlist.append(zoom)
		xlist.append(x)
		ylist.append(y)
		f=df.iloc[i]
		lat_deg,lon_deg=num2deg(f.x0+int(x), f.y0+int(y), int(zoom))
		lat1_deg,lon1_deg=num2deg(f.x1+int(x), f.y1+int(y), int(zoom))
		p1 = geometry.Point(lon_deg,lat_deg,lon_deg)
		p3 = geometry.Point(lon1_deg,lat1_deg)
		p4 = geometry.Point(lon1_deg,lat_deg)
		p2 = geometry.Point(lon_deg,lat1_deg)
		pointList = [p1, p2, p3, p4, p1]
		geomlist.append(geometry.Polygon([[p.x, p.y] for p in pointList]))
		klasslist.append(df.klass.iloc[i])
		scorelist.append(df.score.iloc[i])
		
df_final=pd.DataFrame(
    {'filename': filelist,
     'x': xlist,
     'y': ylist,
     'z': zlist   ,
     'geometry': geomlist,
     'score': scorelist,
     'class': klasslist
    })
    

dt=df_final[df_final['score'] > float(args.thresh)]
dt['class']=dt['class'].astype('int')
dt['class'] = dt['class'].map({0: object_categories[0],1: object_categories[1],
	2: object_categories[2],3:object_categories[3],4:object_categories[4],5:object_categories[5],
	6: object_categories[6],7: object_categories[7],8: object_categories[8],9:object_categories[9],
	10:object_categories[10],11: object_categories[11]})


#gdf = gpd.GeoDataFrame(dt, crs={'init': 'epsg:4326'}, geometry=dt['geometry'])
#gdf.to_file(endpointName+'_025.geojson',driver="GeoJSON")

print('\n\n*********************************************\n')
print('Number of objects detected: ', len(dt))
print('\n')
print('Pole stats: ',dt.groupby('class').count()['score'])
print('\n*********************************************\n')
