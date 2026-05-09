#*****************************************************************************
#
#  System        : 
#  Module        : 
#  Object Name   : $RCSfile$
#  Revision      : $Revision$
#  Date          : $Date$
#  Author        : $Author$
#  Created By    : Robert Heller
#  Created       : 2026-05-08 11:42:13
#  Last Modified : <260508.2022>
#
#  Description	
#
#  Notes
#
#  History
#	
#*****************************************************************************
#
#    Copyright (C) 2026  Robert Heller D/B/A Deepwoods Software
#			51 Locke Hill Road
#			Wendell, MA 01379-9728
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# 
#
#*****************************************************************************


import FreeCAD as App
import Part, TechDraw, TechDrawGui
from FreeCAD import Base

import os
import sys
sys.path.append(os.path.dirname(__file__))
import csv
import math
import Units
from debug import debug
import datetime                                                                 

from debug import debug

from abc import ABCMeta, abstractmethod, abstractproperty

import time
from PySide.QtCore import QCoreApplication, QEventLoop, QTimer

def execute(loop, ms):
    timer = QTimer()
    timer.setSingleShot(True)
    
    timer.timeout.connect(loop.quit)
    timer.start(ms)
    loop.exec_()

def sleep(ms):
    if not QCoreApplication.instance():
        app = QCoreApplication([])
        execute(app, ms)
    else:
        loop = QEventLoop()
        execute(loop, ms)
                                        

#
# CLEAR COPOLYESTER SHEET
# SSC-104   .040" 1.0mm 7"  175mm 12" 300mm
# SSC-10424 .040" 1.0mm 12" 300mm 24" 600mm
#
# WHITE STYRENE PLAIN SHEET
# SSS-10824 .080" 2.0mm 12" 300mm 24" 600mm
#
# PLASTIC PATTERNED SHEET
# .020" thick
# BRICK HO (1:100) SCALE CODE: PS-97 12" x 7" (300mm x 175mm) (RED CLAY)
#
               
class LaserCut(object):
    __mataclass__ = ABCMeta
    @abstractproperty
    def SheetThick(self):
        pass
    @abstractproperty
    def SheetWidth(self):
        pass
    @abstractproperty
    def SheetLength(self):
        pass
    @abstractproperty
    def SheetTemplate(self):
        pass
    __currentSheet = None
    @classmethod
    def Sheet(cls):
        return cls.__currentSheet
    __sheetList    = None
    __currentDocument = None
    @classmethod
    def Document(cls):
        return cls.__currentDocument
    __pageNum = 0
    @classmethod
    def PageNum(cls):
        return cls.__pageNum
    @classmethod
    def IncrPageNum(cls):
        cls.__pageNum += 1
    @classmethod
    def NewPage(cls):
        cls.IncrPageNum()
        page = cls.Document().addObject('TechDraw::DrawPage',"%sPage_%03d"%(cls.__name__,cls.PageNum()))
        page.Template = cls.template
        page.ViewObject.show()
        return page
    def Init(self):
        #debug("*** Testing.Init(%s)",self)
        cls = self.__class__
        if cls.__currentSheet != None:
            __currentSheet.finish()
        cls.__currentSheet = self
        if cls.__sheetList == None:
            cls.__sheetList = list()
        cls.__sheetList.append(self)
        if cls.__currentDocument == None:
            cls.__currentDocument = App.newDocument(cls.__name__)
            cls.template = cls.__currentDocument.addObject('TechDraw::DrawSVGTemplate','CutPanelTemplate')
            cls.template.Template = self.SheetTemplate
        self.page = cls.NewPage()
        
    @classmethod
    def AddCut(cls,shape):
        #debug("%s.AddCut(%s,%s)",cls,cls,shape)
        if cls.__currentSheet == None:
            x = cls.__new__(cls)
            if isinstance(x,cls): x.__init__()
        bb = shape.BoundBox
        debug("*** LaserCut.AddCut(): bb.XLength is %.4f, bb.YLength is %.4f, bb.ZLength is %.4f, ...SheetThick is %.4f",bb.XLength,bb.YLength,bb.ZLength,cls.__currentSheet.SheetThick)
        if round(bb.XLength,3) == round(cls.__currentSheet.SheetThick,3):
            if not cls.__currentSheet.FitP_(bb.YLength,bb.ZLength):
                cls.__currentSheet = cls.__new__()
            cls.__currentSheet.AddCut_(shape,Base.Vector(1,0,0))
        elif round(bb.YLength,3) == round(cls.__currentSheet.SheetThick,3):
            if not cls.__currentSheet.FitP_(bb.XLength,bb.ZLength):
                cls.__currentSheet = cls.__new__()
            cls.__currentSheet.AddCut_(shape,Base.Vector(0,1,0))
        else:
            if not cls.__currentSheet.FitP_(bb.XLength,bb.YLength):
                cls.__currentSheet = cls.__new__()
            cls.__currentSheet.AddCut_(shape,Base.Vector(0,0,1))
    @abstractmethod
    def FitP_(self,XLength,YLength):
        pass
    @abstractmethod
    def AddCut_(self,shape,direction=Base.Vector(0,0,1)):
        pass
    @abstractmethod
    def finish(self):
        pass            
                
            
class CopolysterSSC_104Cut(LaserCut):
    @property
    def SheetThick(self):
        return .040*25.4
    @property
    def SheetWidth(self):
        return 300
    @property
    def SheetLength(self):
        return 175
    @property
    def SheetTemplate(self):
        return os.path.join(os.path.dirname(__file__),"CutPanel300x175.svg")
    def __init__(self):
        self.Init()
        # remaining init...
    def AddCut_(self,shape,direction=Base.Vector(0,0,1)):
        debug("%s.AddCut_(%s,%s,%s)",self.__class__.__name__,self,shape,direction)
        pass
    def FitP_(self,XLength,YLength):
        debug("%s.FitP_(%s,%s,%s)",self.__class__.__name__,self,XLength,YLength)
        return True
    def finish(self):
        debug("%s.finish(%s)",elf.__class__.__name__,self)

class BricksPS_97Cut(LaserCut):
    @property
    def SheetThick(self):
        return .020*25.4
    @property
    def SheetWidth(self):
        return 300
    @property
    def SheetLength(self):
        return 175
    @property
    def SheetTemplate(self):
        return os.path.join(os.path.dirname(__file__),"CutPanel300x175.svg")
    def __init__(self):
        self.Init()
        # remaining init...
    def AddCut_(self,shape,direction=Base.Vector(0,0,1)):
        debug("%s.AddCut_(%s,%s,%s)",self.__class__.__name__,self,shape,direction)
    def FitP_(self,XLength,YLength):
        debug("%s.FitP_(%s,%s,%s)",self.__class__.__name__,self,XLength,YLength)
        return True
    def finish(self):
        debug("%s.finish(%s)",elf.__class__.__name__,self)

class StyreneSSS_10824Cut(LaserCut):
    @property
    def SheetThick(self):
        return .080*25.4
    @property
    def SheetWidth(self):
        return 300
    @property
    def SheetLength(self):
        return 600
    @property
    def SheetTemplate(self):
        return os.path.join(os.path.dirname(__file__),"CutPanel300x600.svg")
    def __init__(self):
        self.Init()
        # remaining init...
    def AddCut_(self,shape,direction=Base.Vector(0,0,1)):
        debug("%s.AddCut_(%s,%s,%s)",self.__class__.__name__,self,shape,direction)
    def FitP_(self,XLength,YLength):
        debug("%s.FitP_(%s,%s,%s)",self.__class__.__name__,self,XLength,YLength)
        return True
    def finish(self):
        debug("%s.finish(%s)",elf.__class__.__name__,self)

