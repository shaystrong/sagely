def ll2subpix(lat,long,zoom):
        import numpy as np
        n = 2 ** zoom
        xtile = n * ((long + 180) / 360)
        ytile = n * (1 - (np.log(np.tan(lat*np.pi/180) + 1/(np.cos(lat*np.pi/180))) / np.pi)) / 2
        fracy,integery=np.modf(ytile)
        fracx,integerx=np.modf(xtile)
        return fracy,integery,fracx,integerx

def tmsVOCxml(dirr,label,joined):
        from xml.etree import ElementTree
        import xml.etree.cElementTree as ET
        if not os.path.exists(dirr):
                os.mkdir(dirr)
        if not os.path.exists(dirr+"Annotations/"):
                os.mkdir(dirr+"Annotations/")
        if not os.path.exists(dirr+"JPEGImages/"):
                os.mkdir(dirr+"JPEGImages/")
        joined['imagename']=joined.z+'_'+joined.x+'_'+joined.y
        gg= joined.groupby('imagename')
        listt=list(gg.groups.keys())
        for i in range(0,len(listt)):
                imagename=listt[i]
                classes = [label]
                top = ElementTree.Element('Annotation')
                folder = ElementTree.SubElement(top,'folder')
                folder.text = dirr.split('/')[-2]     #e.g. 'VOC1800'
                filename = ElementTree.SubElement(top,'filename')
                filename.text = imagename + 'jpg'
                path = ElementTree.SubElement(top, 'path')
                path.text= dirr+'JPEGImages/'+imagename+ '.jpg'
                use=gg.get_group(listt[i])
                #print(use[['minx', 'miny', 'maxx', 'maxy']])
                #print(use[['pix_minx', 'pix_miny', 'pix_maxx', 'pix_maxy']])
                for h in range(0,len(use)):
                        boxCoords=[use.pix_minx.iloc[h],use.pix_miny.iloc[h],use.pix_maxx.iloc[h],use.pix_maxy.iloc[h],use['class'].iloc[h]]
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

def supermercado_labels(df,zoom):
        import geopandas as gpd
        import os
        os.system('cat box_labels.geojson | supermercado burn '+str(zoom)+' | mercantile shapes | fio collect > box_labels_supermarket.geojson')   #create a geojson of tms tiles
        print('supermercado tile geojson created... ','box_labels_supermarket.geojson')
        superm = gpd.GeoDataFrame.from_file('box_labels_supermarket.geojson')
        label = gpd.GeoDataFrame.from_file('box_labels.geojson')
        joined=gpd.sjoin(label,superm,op='intersects')
        j=joined.title.str.split(' ',expand=True).add_prefix('tms')
        joined['x']=j['tms2'].map(lambda x: x.lstrip('(,)').rstrip('(,)'))
        joined['y']=j['tms3'].map(lambda x: x.lstrip('(,)').rstrip('(,)'))
        joined['z']=j['tms4'].map(lambda x: x.lstrip('(,)').rstrip('(,)'))
        joined=joined[['class', 'geometry', 'x', 'y', 'z']]
        market_labels='box_labels_marketlabeled.geojson'
        joined['minx'],joined['miny'],joined['maxx'],joined['maxy']=joined.bounds.minx,joined.bounds.miny,joined.bounds.maxx,joined.bounds.maxy
        joined['fracminy'],integerminy,joined['fracminx'],integerminx=ll2subpix(joined['miny'],joined['minx'],zoom)
        joined['fracmaxy'],integermaxy,joined['fracmaxx'],integermaxx=ll2subpix(joined['maxy'],joined['maxx'],zoom)
        joined['pix_maxx']=(joined['fracmaxx']*256).astype('int')
        joined['pix_minx']=(joined['fracminx']*256).astype('int')
        joined['pix_maxy']=(joined['fracmaxy']*256).astype('int')
        joined['pix_miny']=(joined['fracminy']*256).astype('int')
        joined.drop(joined[joined.pix_maxy < joined['pix_miny']].index, inplace=True)
        joined.drop(joined[joined.pix_maxx < joined['pix_maxy']].index, inplace=True)
        try:
                joined.to_file(market_labels,driver='GeoJSON')
        except Exception as e:
                print('file exists, overwriting')
                os.system('rm '+market_labels)
                joined.to_file(market_labels,driver='GeoJSON')
        return joined
        
def cleanupPairs(pathh):
        import glob
        for i in glob.glob(pathh+'Annotations/'+'*xml'):
                filename_split = os.path.splitext(i)
                filename_zero, fileext = filename_split
                basename = os.path.basename(filename_zero)
                if  not os.path.isfile(pathh+'JPEGImages/'+basename+'.jpg'):
                        os.system('rm '+i)
        for i in glob.glob(pathh+'JPEGImages/'+'*jpg'):
                filename_split = os.path.splitext(i)
                filename_zero, fileext = filename_split
                basename = os.path.basename(filename_zero)
                if  not os.path.isfile(pathh+'Annotations/'+basename+'.xml'):
                	os.system('rm '+i)
                
def flattenTMS(tilepath,zoom,voc): #flatten the TMS tile structure to put all images in one directory e.g. tilepath='tiles', zoom='18'
	import glob,os
	for i in glob.glob(tilepath+'/'+zoom+'/*/*png'):
		filename_split = os.path.splitext(i)
		filename_zero, fileext = filename_split
		basename = os.path.basename(filename_zero)
		strn=i.split('/')[-3]+'_'+i.split('/')[-2]+'_'+i.split('/')[-1]
		#write_xml_annotation(strn, boxCoords)
		if not os.path.exists(voc+'JPEGImages/'):
			os.mkdir(tilevocath+'JPEGImages/')
		os.system('cp '+i+' '+voc+'JPEGImages/'+strn)
		os.system('mogrify -format jpg '+voc+'JPEGImages/*.png')
		os.system('rm '+voc+'JPEGImages/*.jpg')

def footprint2box(vector):
	df = vector  
	df['geometry']=df.envelope      #round to nearest (axis-aligned_ rectangle
	#df.to_file('box_labels.geojson',driver='GeoJSON')
	df['class']='building'  #all buildings we will just call class=buildings
	return df

#df=footprint2box(buildings)