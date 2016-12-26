# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : img_normdiff
Description          : Class for calculate Normalize Difference

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
import warnings, numpy as np
from osgeo import gdal

import util
if not util.QUIET_GDAL_EXCEPTIONS:
  util.quietGdalExceptions()

class NormalizeDifference:
  def __init__(self, params):
    """
    Keys of params:
      'dirOut': Diretory for save files
      'ds': Dataset
      'numB1': number of band 1
      'numB2': number of band 2
    """
    self.params = params
    self.paramsOut, self.nameFileND, self.dataND = None, None, None

  def __del__(self):
    self.dataND, self.paramsOut = None, None

  def _writeDataset(self, typeImage, dataImage, nodata, pathfileOut=None):
    args, drv = None, None
    if not pathfileOut is None:
      util.removeImage( pathfileOut )
      args = ( pathfileOut, self.paramsOut['xsize'], self.paramsOut['ysize'], 1, typeImage )
      drv = gdal.GetDriverByName('GTiff')
    else:
      drv = gdal.GetDriverByName('MEM')
      args = ( '', self.paramsOut['xsize'], self.paramsOut['ysize'], 1, typeImage )
      
    dsOut = drv.Create( *args )
    dsOut.SetGeoTransform( self.paramsOut['transform'] )
    dsOut.SetProjection( self.paramsOut['proj4'] )
    band = dsOut.GetRasterBand( 1 )
    dataImage[ dataImage == np.nan ] = nodata
    band.WriteArray( dataImage )
    band.SetNoDataValue( nodata )
    band.FlushCache()
    dsOut.FlushCache()
    return dsOut 

  def init(self):
    def checkNumbersBand():
      def checkNumber(lb , nb):
        if nb > totalBands:
          msg = "Band {l} '{n}' is upper than {t}(total bands)".format( l=lb, n=nb, t=totalBands )
          return { 'isOk': False, 'msg': msg}
        return { 'isOk': True }

      totalBands = self.params['ds'].RasterCount
      for t in ( ( 1, self.params['numB1'] ), ( 2 , self.params['numB2'] ) ):
        r = checkNumber(t[0] , t[1] )
        if not r['isOk']:
          return r
      return { 'isOk': True }
    
    r = checkNumbersBand()
    if not r['isOk']:
      return r 
   
    self.paramsOut = {
      'transform': self.params['ds'].GetGeoTransform(),
      'proj4': self.params['ds'].GetProjection(),
      'xsize': self.params['ds'].RasterXSize,
      'ysize': self.params['ds'].RasterYSize
    }
    nameSource = os.path.basename( self.params['ds'].GetDescription() )
    args = ( self.params['numB1'], self.params['numB2'] )
    suffix = "_ndwi_B{0}B{1}.tif".format( *args )
    self.nameFileND = nameSource.replace( ".tif", suffix )
    self.nameFileND = "{d}{s}{n}".format( d=self.params['dirOut'], s=os.path.sep, n=self.nameFileND )
    warnings.filterwarnings("ignore") # Operators by NumPy
    return { 'isOk': True }

  def createND(self):
    def getDataND():
      ysize, xsize = self.params['ds'].RasterYSize, self.params['ds'].RasterXSize
      d = np.ndarray( ( ysize, xsize ), dtype=np.float )
      d.fill( np.nan )
      b1 = self.params['ds'].GetRasterBand( self.params['numB1'] )
      b2 = self.params['ds'].GetRasterBand( self.params['numB2'] )
      for yoff in xrange( ysize ):
        d1 = b1.ReadAsArray( 0, yoff, xsize, 1 ).astype(np.float)
        d2 = b2.ReadAsArray( 0, yoff, xsize, 1 ).astype(np.float)
        d[yoff] = ( d1 - d2 ) / ( d1 + d2 )
      return d
    
    dsND = None
    self.dataND = getDataND()
    args = ( self.params['numB1'], self.params['numB2'] )
    args = [ gdal.GDT_Float32, self.dataND, -999, self.nameFileND ]
    try:
      dsND = self._writeDataset( *args )
    except RuntimeError as e:
      msg = "'{s}': {m}".format( s="Trying create ND", m=str(e) )
      return { 'isOk': False, 'msg': msg }
    dsND = None
    return { 'isOk': True }

  def getNameLimit(self, limit):
    v_abs = abs( limit )
    signal = ''
    if limit == 0:
      signal = 'o'
    elif limit < 0:
      signal = 'n'
    else:
      signal = 'p'
    prefix = "{0}{1:.3f}".format( signal, v_abs ).replace('.', '_')
    return self.nameFileND.replace( ".tif", "_{0}".format( prefix ) )

  def getDSLimit(self, limit, min_pixels, has_diagonal_connect=False):
    def getDataLimit():
      data = np.zeros( self.dataND.shape )
      data[ self.dataND >= limit ] = 1
      return data

    def getDataSieve(data):
      def getDatasetByte():
        drv = gdal.GetDriverByName("MEM")
        ysize, xsize = data.shape
        dataDrive = ( '', xsize, ysize, 2, gdal.GDT_Byte )
        ds = drv.Create( *dataDrive )
        return ds
      
      ds = getDatasetByte()
      band_origin = ds.GetRasterBand(1)
      band_origin.WriteArray( data )
      band_sieve = ds.GetRasterBand(2)
      c = 8 if has_diagonal_connect else 4
      try:
        gdal.SieveFilter( band_origin, None, band_sieve, min_pixels, c, [], callback=None )
      except RuntimeError:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
      data_sieve = band_sieve.ReadAsArray()
      ds = None
      return { 'isOk': True, 'data_sieve': data_sieve }
      
    r = getDataSieve( getDataLimit() )
    if not r['isOk']:
      return r
    args = [ gdal.GDT_Byte, r['data_sieve'], 0 ]
    ds = None
    try:
      ds = self._writeDataset( *args )
    except RuntimeError as e:
      msg = "Trying create Class for limit '{0}'".format(limit)
      msg = "'{s}': {m}".format( s=msg, m=str(e) )
      return { 'isOk': False, 'msg': msg }

    return { 'isOk': True, 'ds': ds }
