# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : logprocess
Description          : Class for log of processing

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

import sys
from datetime import datetime

class LogProcess:
  f_time = "%Y-%m-%d %H:%M:%S"
  def __init__(self, pathfile, start_end=True):
    self.start_end = start_end
    self.filelog = open( pathfile, "a" )
    if self.start_end:
      self.timeInit = datetime.now()
      stime = self.timeInit.strftime( LogProcess.f_time )
      self.filelog.write("Started: {0}\n".format( stime ) )
      self.filelog.flush()

  def __del__(self):
    if self.start_end:
      timeEnd = datetime.now()
      stime = timeEnd.strftime( LogProcess.f_time )
      delta = timeEnd - self.timeInit
      sdelta = str( delta ).split('.')[0]
      args = ( stime, sdelta )
      self.filelog.write("Finished: {0}(total time {1})\n".format( *args ) )
      self.filelog.flush()
    self.filelog.close()
  
  def write(self, msg, time=False,end=False):
    suffixEnd = '\n' if end else ''
    if time:
      stime = datetime.now().strftime( self.f_time )
      suffixEnd = " - ({0}){1}".format( stime, suffixEnd )
    
    self.filelog.write("{0}{1}".format( msg, suffixEnd) )
    self.filelog.flush()
