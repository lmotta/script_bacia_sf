# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : polygonize_mask
Description          : Class for polygonize mask image(dataset)

                       -------------------
Begin                : 2016-12-26
Copyright            : (C) 2016 by Luiz Motta
Email                : motta dot luiz at gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from osgeo import gdal, ogr, osr

import util
if not util.QUIET_GDAL_EXCEPTIONS:
  util.quietGdalExceptions()

class PolygonizeMask:
  def __init__(self):
    self.drvMem = ogr.GetDriverByName("MEMORY")
    self.drvShp = ogr.GetDriverByName("ESRI Shapefile")
  
  def create(self, shapefile, dsImg):
    def createLayerMask():
      srs = osr.SpatialReference()
      srs.ImportFromWkt( dsImg.GetProjectionRef() )
      ds = self.drvMem.CreateDataSource( 'memory' )
      nameLayer = os.path.basename( shapefile ).split('.')[0]
      layer = ds.CreateLayer( nameLayer, srs)
      return ds, layer

    def addArea():
      f_area = ogr.FieldDefn("area", ogr.OFTReal)
      layer.CreateField( f_area )
      for feat in layer:
        area = feat.GetGeometryRef().GetArea()
        feat.SetField( "area", area )
        layer.SetFeature( feat )
        feat.Destroy()
      dsLayer.FlushCache()
    
    dsLayer, layer = createLayerMask()
    band = dsImg.GetRasterBand(1)
    gdal.Polygonize( band, band, layer, -1, [], callback=None )
    addArea()
    
    ds = self.drvShp.CopyDataSource( dsLayer, shapefile )
    dsLayer.Destroy()
    ds.Destroy()
    
    return { 'isOk': True }
