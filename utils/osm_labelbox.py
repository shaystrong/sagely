import pycrs, os
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from xml.etree import ElementTree
import xml.etree.cElementTree as ET


class cdragon(object):
	def __init__(self,zoom,epsg,osm_vector,img):
		self.zoom=zoom
		self.epsg=epsg
		self.osm_vector=osm_vector
		self.img=img
		
	def getFeatures(self,roi_vector):    
		gdf = gpd.GeoDataFrame.from_file(roi_vector)
		"""Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
		import json
		try:
			f= [json.loads(gdf.to_json())['features'][0]['geometry']]    #currently just expecting a single ROI
		except Exception as e:
			print(e)
			f=''
		return f
	def flattenTMS(tilepath,zoom):
		"""flatten the TMS tile structure to put all images in one directory
			e.g. tilepath='rockport_dg_image_2017', zoom='18'"""
		import glob,os
		for i in glob.glob(tilepath+'/'+zoom+'/*/*png'):
			filename_split = os.path.splitext(i)
			filename_zero, fileext = filename_split
			basename = os.path.basename(filename_zero)
			strn=i.split('/')[-3]+'_'+i.split('/')[-2]+'_'+i.split('/')[-1]
			#write_xml_annotation(strn, boxCoords)
			if not os.path.exists(tilepath+'_flatten/'):
				os.mkdir(tilepath+'_flatten/')
			os.system('cp '+i+' '+tilepath+'_flatten/'+strn)
	def getImageClip(coords,img,outRGB,i):
		data = rasterio.open(img)
		try:
			out_img, out_transform = mask(data,coords, crop=True)
			out_meta = data.meta.copy()
			out_meta.update({"driver": "GTiff","height": out_img.shape[1],"width": out_img.shape[2],"transform": out_transform,"crs": pycrs.parse.from_epsg_code('4326').to_proj4()})
			if not os.path.exists(outRGB):
				os.mkdir(outRGB)
			if not os.path.isfile(outRGB+'rockport_training_data'+'_'+str(i)+'.tif'):
				with rasterio.open(outRGB+'rockport_training_data'+'_'+str(i)+'.tif', 'w',**out_meta) as dest:   
					dest.write(out_img)
		except Exception as e:
			print(e)
		return

	def boxClipDF(df,img,outRGB):
	#  clip geoemtries out of large image tif and save as small tif
		for i in range(0,len(df)):
			coords = getFeatures(df,i)
			getImageClip(coords,img,outRGB,i)
	def ll2subpix(self,lat,long):
		import numpy as np
		n = 2 ** self.zoom
		xtile = n * ((long + 180) / 360)
		ytile = n * (1 - (np.log(np.tan(lat*np.pi/180) + 1/(np.cos(lat*np.pi/180))) / np.pi)) / 2
		fracy,integery=np.modf(ytile)
		fracx,integerx=np.modf(xtile)
		return fracy,integery,fracx,integerx
	def footprint2box(self):
		df = self.osm_vector  #gpd.GeoDataFrame.from_file(self.osm_vector)
		#df['geometry']=df['geometry'].buffer(5e-5)			#buffer in case aligned vector doesn't match underlying raster
		df['geometry']=df.envelope      				#round to nearest (axis-aligned_ rectangle
		self.boxes=df
		#save osm enveloped rectanngles
		#df.to_file(out_osm_rect_vector,driver='GeoJSON')
		return df
	def joinOSM_with_label(self):
		label = gpd.GeoDataFrame.from_file(self.label_vector)
		traindf=gpd.sjoin(self.boxes,label,how='left')   										#merge on OSM buildings. Get the damage intersectionn with the building. keep everything
		traindf['damage']=traindf['damage'].fillna(0).astype('int')
		traindf['damage_lvl']=traindf['Damage_Lvl'].fillna(0).astype('int')
		trainfinal=traindf[['damage','damage_lvl','geometry']]       
		trainfinal = trainfinal.set_geometry('geometry')
		df=trainfinal['geometry'].buffer(1e-3)	
		df=df.to_frame()
		df.columns = ['geometry']
		df=df.set_geometry('geometry')
		self.trainfinal=trainfinal.set_geometry('geometry')
		filename_split = os.path.splitext(self.img)
		self.osm_label_geojson=filename_split[0]+'_osmlabeled.geojson'
		try:
			self.trainfinal.to_file(filename_split[0]+'_osmlabeled.geojson',driver='GeoJSON')
		except Exception as e:
			print('file exists, overwriting')
			os.system('rm '+filename_split[0]+'_osmlabeled.geojson')
			self.trainfinal.to_file(filename_split[0]+'_osmlabeled.geojson',driver='GeoJSON')
		print('Created geojson of labelled OSM buildings... ', filename_split[0]+'_osmlabeled.geojson')
	def supermercado_labels(self):
		filename_split = os.path.splitext(self.osm_label_geojson)
		os.system('cat '+self.osm_label_geojson+' | supermercado burn '+str(self.zoom)+' | mercantile shapes | fio collect > '+filename_split[0]+'_market.geojson')   #create a geojson of tms tiles
		print('supermercado tile geojson created... ',filename_split[0]+'_market.geojson')
		superm = gpd.GeoDataFrame.from_file(filename_split[0]+'_market.geojson')
		label = gpd.GeoDataFrame.from_file(self.osm_label_geojson)
		joined=gpd.sjoin(label,superm,op='intersects')  
		j=joined.title.str.split(' ',expand=True).add_prefix('tms')
		joined['x']=j['tms2'].map(lambda x: x.lstrip('(,)').rstrip('(,)'))
		joined['y']=j['tms3'].map(lambda x: x.lstrip('(,)').rstrip('(,)'))
		joined['z']=j['tms4'].map(lambda x: x.lstrip('(,)').rstrip('(,)'))
		joined=joined[['damage', 'damage_lvl', 'geometry', 'x', 'y', 'z']]
		self.market_labels=filename_split[0]+'_marketlabeled.geojson'
		try:
			joined.to_file(self.market_labels,driver='GeoJSON')
		except Exception as e:
			print('file exists, overwriting')
			os.system('rm '+self.market_labels)
			self.trainfinal.to_file(self.market_labels,driver='GeoJSON')
		joined['minx'],joined['miny'],joined['maxx'],joined['maxy']=joined.bounds.minx,joined.bounds.miny,joined.bounds.maxx,joined.bounds.maxy
		fracminy,integerminy,fracminx,integerminx=self.ll2subpix(joined['miny'],joined['minx'])
		fracmaxy,integermaxy,fracmaxx,integermaxx=self.ll2subpix(joined['maxy'],joined['maxx'])
		joined['pix_maxx']=(fracmaxx*256).astype('int')
		joined['pix_minx']=(fracminx*256).astype('int')
		joined['pix_maxy']=(fracmaxy*256).astype('int')
		joined['pix_miny']=(fracminy*256).astype('int')
		self.joined = joined[joined.damage != 0]
	def tmsVOCxml(self,dirr):
		if not os.path.exists(dirr):
			os.mkdir(dirr)
			os.mkdir(dirr+"Annotations/")
			os.mkdir(dirr+"JPEGImages/")
		self.joined['imagename']=self.joined.z+'_'+self.joined.x+'_'+self.joined.y
		gg= self.joined.groupby('imagename')
		listt=list(gg.groups.keys())
		for i in range(0,len(listt)):
			imagename=listt[i]
			classes = ['damage']
			top = ElementTree.Element('Annotation')
			folder = ElementTree.SubElement(top,'folder')
			folder.text = dirr.split('/')[-2]     #e.g. 'VOC1800'
			filename = ElementTree.SubElement(top,'filename')
			filename.text = imagename + 'jpg'
			path = ElementTree.SubElement(top, 'path')
			path.text= dirr+'JPEGImages/'+imagename+ '.jpg'
			use=gg.get_group(listt[i])
			print(use[['minx', 'miny', 'maxx', 'maxy']])
			print(use[['pix_minx', 'pix_miny', 'pix_maxx', 'pix_maxy']])
			for h in range(0,len(use)):
				boxCoords=[use.pix_minx.iloc[h],use.pix_miny.iloc[h],use.pix_maxx.iloc[h],use.pix_maxy.iloc[h],use.damage.iloc[h]]
				objects = ElementTree.SubElement(top, 'object')
				childchild = ElementTree.SubElement(objects,'name')
				childchild.text = classes[0]
				secondchild = ElementTree.SubElement(objects,'bndbox')
				grandchild1 = ElementTree.SubElement(secondchild, 'xmin')
				grandchild1.text= str(abs(boxCoords[0]))
				grandchild2 = ElementTree.SubElement(secondchild, 'ymin')
				grandchild2.text = str(boxCoords[1])
				grandchild3 = ElementTree.SubElement(secondchild, 'xmax')
				grandchild3.text = str(abs(boxCoords[2]))
				grandchild4 = ElementTree.SubElement(secondchild, 'ymax')
				grandchild4.text = str(boxCoords[3])
			size = ElementTree.SubElement(top,'size')
			width = ElementTree.SubElement(size, 'width')
			width.text = str(256)
			height = ElementTree.SubElement(size, 'height')
			height.text = str(256)
			depth = ElementTree.SubElement(size, 'depth')
			depth.text = str(3)
			tree = ET.ElementTree(top)
			tree.write(dirr+"Annotations/"+imagename+".xml")

def	cleanupPairs(pathh):
	for i in glob.glob(pathh+'Annotations/'+'*xml'):
		filename_split = os.path.splitext(i)
		filename_zero, fileext = filename_split
		basename = os.path.basename(filename_zero)
		if  not os.path.isfile(pathh+'JPEGImages/'+basename+'.png'): 
			os.system('rm '+i)


