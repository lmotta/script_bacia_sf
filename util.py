# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : util
Description          : Generic functions

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

import os,sys 

QUIET_GDAL_EXCEPTIONS = False
def quietGdalExceptions():
  if 'osgeo' in sys.modules:
    sys.modules['osgeo'].gdal.UseExceptions()
    sys.modules['osgeo'].gdal.PushErrorHandler('CPLQuietErrorHandler')
    QUIET_GE = True

def hasCreatePermission(pathfile,isDir=False):
  vpath = os.path.dirname( pathfile ) if not isDir else pathfile
  if not os.access( vpath, os.W_OK ):
    msg = "Not have permission for create '{f}'".format( f=pathfile )
    return { 'isOk': False, 'msg': msg }
  return { 'isOk': True }

def removeImage(pathfile):
  if os.path.isfile( pathfile):
    os.remove( pathfile )
  auxfile = "{f}.aux.xml".format( f=pathfile )
  if os.path.isfile( auxfile ):
    os.remove( auxfile )

def getValueFormatArgs( args):
  f = ''.join( [ ( "{%d}" % i ) for i in range( len( args ) ) ] )
  return f.format( *args )
