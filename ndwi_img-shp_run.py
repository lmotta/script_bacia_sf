#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : ndwi_img-shp_run
Description          : Create set of files(image and shapefile) with NDWI values
Arguments            : image, band1, band2, limits(separate by comma), 
                       minimal_area(pixels), directory for result

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

import sys, os, argparse

from osgeo import gdal
import util
if not util.QUIET_GDAL_EXCEPTIONS:
  util.quietGdalExceptions()

from img_normdiff import NormalizeDifference
from polygonize_mask import PolygonizeMask
from logprocess import LogProcess

def run(pathfile, numB1, numB2, limits, min_pixels, dirOut):
  def checkArgs():
    def getValueLimits():
      values = None
      try:
        values = [ float(v) for v in limits.split(',') ]
      except ValueError as e:
        return { 'isOk': False, 'msg': str(e) }
      return { 'isOk': True, 'values': values }
  
    if not os.path.isfile( pathfile ):
      msg = "Missing file '{0}'".format( pathfile)
      return { 'isOk': False, 'msg': msg }
  
    if not os.path.isdir( dirOut ):
      msg = "Missing directory '{0}'".format( dirOut)
      return { 'isOk': False, 'msg': msg }

    r = util.hasCreatePermission( dirOut )
    if not r['isOk']:
      return r
  
    r = getValueLimits()
    if not r['isOk']:
      return r

    return { 'isOk': True, 'values_limit': r['values'] }

  def createNDWI( pathfile, log ):
    def getDirOut(nameImg):
      nameTileID = nameImg.split('_')[0]
      args = ( params['dirOut'], os.sep, nameTileID, os.sep )
      dirOut = util.getValueFormatArgs( args )
      if not os.path.isdir( dirOut ):
        os.makedirs( dirOut )
      return dirOut

    nameImg = os.path.basename( pathfile )
    nameImg = os.path.splitext( nameImg )[0]
    ds_pathfile = None
    try:
      ds_pathfile = gdal.Open( pathfile )
    except RuntimeError as e:
      msg = "{0} - {1}".format( nameImg, str( e ) )
      log.write( msg, end=True )
      return
    paramsND = {
      'ds': ds_pathfile,
      'numB1': params['numB1'],
      'numB2': params['numB2']
    }
    paramsND['dirOut'] = getDirOut(nameImg)
    nd = NormalizeDifference( paramsND )
    r = nd.init()
    if not r['isOk']:
      msg = "{0} - {1}".format( nameImg, r['msg'] )
      log.write( msg, end=True )
      return
    r = nd.createND()
    if not r['isOk']:
      msg = "{0} - {1}".format( nameImg, r['msg'] )
      log.write( msg, end=True )
      return
    ds_pathfile = None
    extMinPixel = "_{0}px.shp".format( params['min_pixels'] )
    pm = PolygonizeMask()
    for limit in params['limits']:
      shapefile = "{0}.shp".format( nd.getNameLimit( limit ) )
      r = nd.getDSLimit( limit, 2, True)
      if not r['isOk']:
        args = ( nameImg, limit, r['msg'] )
        msg = "{0} - Limit '{1}' - {2}".format( *args )
        log.write( msg, end=True )
        return
      r = pm.create( shapefile, r['ds']  )
      if not r['isOk']:
        args = ( nameImg, limit, r['msg'] )
        msg = "{0} - Limit '{1}' - {2}".format( *args )
        log.write( msg, end=True )
        return
      r['ds'] = None
      # Remove min_pixels
      shapefile = shapefile.replace( ".shp", extMinPixel )
      r = nd.getDSLimit( limit, params['min_pixels'] )
      if not r['isOk']:
        args = ( nameImg, limit, params['min_pixels'], r['msg'] )
        msg = "{0} - Limit '{1}' - {2} pixels - {3}".format( *args )
        log.write( msg, end=True )
        return
      r = pm.create( shapefile, r['ds'] )
      if not r['isOk']:
        args = ( nameImg, limit, params['min_pixels'], r['msg'] )
        msg = "{0} - Limit '{1}' - {2} pixels - {3}".format( *args )
        log.write( msg, end=True )
        return
      r['ds'] = None

    msg = "{0} - {1}".format( nameImg, 'OK' )
    log.write( msg, end=True )
  
  r = checkArgs()
  if not r['isOk']:
    sys.stderr.write( r['msg'] )
    return 1
  values = r['values_limit']

  log_file = "/home/lmotta/data/bacia_sao-francisco/temp/test/ndwi_img-shp_multi_run.log"
  log = LogProcess( log_file)
  params = {
    'numB1': numB1, 'numB2': numB2,
    'limits': r['values_limit'],
    'min_pixels': min_pixels,
    'dirOut': dirOut
  }
  createNDWI( pathfile, log )

  return 0

def main():
  d = "Normalized difference and classification - (B1 - B2) / (B1 + B2)."
  parser = argparse.ArgumentParser(description=d )
  d = "Pathfile of image"
  parser.add_argument('pathfile', metavar='pathfile', type=str, help=d )
  d = "Number of Band 1"
  parser.add_argument('numB1', metavar='B1', type=int, help=d )
  d = "Number of Band 2"
  parser.add_argument('numB2', metavar='B2', type=int, help=d )
  d = "Limits break(use comma how separator, Ex: '0,0.01,0.005' )"
  parser.add_argument('limits', metavar='limits', type=str, help=d )
  d = "Minimum area(pixels)"
  parser.add_argument('min_pixels', metavar='min_pixels', type=int, help=d )
  d = "Diretory for write files"
  parser.add_argument('dirOut', metavar='dirOut', type=str, help=d )

  args = parser.parse_args()
  return run( args.pathfile, args.numB1, args.numB2, args.limits, args.min_pixels, args.dirOut )

if __name__ == "__main__":
    sys.exit( main() )
