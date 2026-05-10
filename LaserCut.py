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
#  Last Modified : <260510.1250>
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
    __objNum = 0
    @classmethod 
    def ObjName(cls):
        return "Obj%04d"%(cls.__objNum)
    @classmethod
    def IncrObjNum(cls):
        cls.__objNum += 1
    @classmethod
    def NewPage(cls):
        cls.IncrPageNum()
        name = "%sPage_%03d"%(cls.__name__,cls.PageNum())
        page = cls.Document().addObject('TechDraw::DrawPage',name)
        page.Template = cls.template
        page.ViewObject.show()
        #debug("*** LaserCut.NewPage(%s): returning (%s, %s)"%(cls,page,name+'.svg'))
        return (page, name+'.svg')
    def Init(self):
        #debug("*** Testing.Init(%s)"%(self))
        cls = self.__class__
        if cls.__currentSheet != None:
            #debug("*** Testing.Init(%s): cls.__currentSheet is %s"%(self,cls.__currentSheet))
            cls.__currentSheet.finish()
        cls.__currentSheet = self
        if cls.__sheetList == None:
            cls.__sheetList = list()
        cls.__sheetList.append(self)
        if cls.__currentDocument == None:
            cls.__currentDocument = App.newDocument(cls.__name__)
            cls.template = cls.__currentDocument.addObject('TechDraw::DrawSVGTemplate','CutPanelTemplate')
            cls.template.Template = self.SheetTemplate
        self.page, self.filename = self.NewPage()
        self.lastX = 6.35
        self.lastY = 6.35
        self.deltaY = 0
        #debug("*** Testing.Init(%s): self.lastX is %.4f, self.lastY is %.4f, self.deltaY is %.4f"%(self,self.lastX ,self.lastY,self.deltaY))   
    @classmethod
    def AddCut(cls,shape,dir=1,rotatable=True):
        #debug("%s.AddCut(%s,%s)",cls,cls,shape)
        if cls.__currentSheet == None:
            x = cls.__new__(cls)
            if isinstance(x,cls): x.__init__()
        bb = shape.BoundBox
        #debug("*** LaserCut.AddCut(): bb.XLength is %.4f, bb.YLength is %.4f, bb.ZLength is %.4f, ...SheetThick is %.4f",bb.XLength,bb.YLength,bb.ZLength,cls.__currentSheet.SheetThick)
        if round(bb.XLength,3) == round(cls.__currentSheet.SheetThick,3):
            if cls.__currentSheet.__AddCut(shape,Base.Vector(dir,0,0),rotatable):
                return
            x = cls.__new__(cls)
            if isinstance(x,cls): x.__init__()
            if not cls.__currentSheet.__AddCut(shape,Base.Vector(dir,0,0),rotatable):
                raise RuntimeError("Can't add cut: XLength is %.4f, YLength is %.4f, ZLength is %.4f, Sheet Type is %s",bb.XLength,bb.YLength,bb.ZLength,cls.__name_)
        elif round(bb.YLength,3) == round(cls.__currentSheet.SheetThick,3):
            if cls.__currentSheet.__AddCut(shape,Base.Vector(0,dir,0),rotatable):
                return
            x = cls.__new__(cls)
            if isinstance(x,cls): x.__init__()
            if not cls.__currentSheet.__AddCut(shape,Base.Vector(0,dir,0),rotatable):
                raise RuntimeError("Can't add cut: XLength is %.4f, YLength is %.4f, ZLength is %.4f, Sheet Type is %s",bb.XLength,bb.YLength,bb.ZLength,cls.__name_)
        else:
            if cls.__currentSheet.__AddCut(shape,Base.Vector(0,0,dir),rotatable):
                return
            x = cls.__new__(cls)
            if isinstance(x,cls): x.__init__()
            if not cls.__currentSheet.__AddCut(shape,Base.Vector(0,0,dir),rotatable):
                raise RuntimeError("Can't add cut: XLength is %.4f, YLength is %.4f, ZLength is %.4f, Sheet Type is %s",bb.XLength,bb.YLength,bb.ZLength,cls.__name_)
    @staticmethod
    def FitPanelRotatable(lastX,lastY,lengthX,lengthY,deltaY,minX,minY,maxX,maxY):
        currentX = lastX
        currentY = lastY
        rotation = 0
        if (lengthY > 2*deltaY and lengthX < deltaY) or \
            lengthY > lengthX*2:
            temp = lengthX
            lengthX = lengthY
            lengthY = temp
            rotation = 90
        if currentX+lengthX < maxX and \
           currentY+lengthY < maxY:
            #debug("*** LaserCut.FitPanelRotatable(A): deltaY = ",deltaY,", lengthY = ",lengthY)
            deltaY = max(deltaY,lengthY+10)
            return (True, currentX, currentY, lengthX, lengthY, deltaY, rotation)
        elif currentX+lengthX > maxX and \
           currentY+lengthY+deltaY < maxY and \
           minX+lengthX < maxX:
            currentX = minX
            currentY += deltaY
            return (True, currentX, currentY, lengthX, lengthY+10, deltaY, rotation)
        elif currentY+lengthY > maxY and \
             currentY+lengthX < maxY and \
             currentX+lengthY < maxX:
            temp = lengthX
            lengthX = lengthY
            lengthY = temp
            if rotation == 0:
                rotation = 90
            else:
                rotation = 0
            #debug("*** LaserCut.FitPanelRotatable(B): deltaY = ",deltaY,", lengthY = ",lengthY)
            deltaY = max(deltaY,lengthY+10)
            return (True, currentX, currentY, lengthX, lengthY, deltaY, rotation)
        elif currentY+deltaY+lengthX < maxY and \
             minX+lengthY < maxX:
            temp = lengthX
            lengthX = lengthY
            lengthY = temp
            if rotation == 0:
                rotation = 90
            else:
                rotation = 0
            currentX = minX
            currentY += deltaY
            return (True, currentX, currentY, lengthX, lengthY+10, deltaY, rotation)
        else:
            return (False, lastX, lastY, lengthX, lengthY, deltaY, rotation)
    @staticmethod
    def FitPanelNonRotatable(lastX,lastY,lengthX,lengthY,deltaY,minX,minY,maxX,maxY):
        currentX = lastX
        currentY = lastY
        rotation = 0
        if currentX+lengthX < maxX and \
           currentY+lengthY < maxY:
            #debug("*** LaserCut.FitPanelNonRotatable(A): deltaY = ",deltaY,", lengthY = ",lengthY)
            deltaY = max(deltaY,lengthY+3.175)
            return (True, currentX, currentY, lengthX, lengthY, deltaY, rotation)
        elif currentX+lengthX > maxX and \
           currentY+lengthY+deltaY < maxY and \
           minX+lengthX < maxX:
            currentX = minX
            currentY += deltaY
            return (True, currentX, currentY, lengthX, lengthY+3.175, deltaY, rotation)
        else:
            return (False, lastX, lastY, lengthX, lengthY, deltaY, rotation)
    def __AddCut(self,shape,direction=Base.Vector(0,0,1),rotatable=True):
        #debug("*** LaserCut.__AddCut(%s,%s,%s,%s)"%(self,shape,direction,rotatable))
        bbox = shape.BoundBox
        minX = 6.35
        minY = 6.35
        maxX = self.SheetWidth-6.35
        maxY = self.SheetLength-6.35
        lengthX = 0
        lengthY = 0
        if direction.x != 0:
            lengthX = bbox.YLength
            lengthY = bbox.ZLength
        elif direction.y != 0:
            lengthX = bbox.XLength
            lengthY = bbox.ZLength
        else: # direction.z != 0
            lengthX = bbox.XLength
            lengthY = bbox.YLength
        if rotatable:
            fitP, currentX, currentY, lengthX, lengthY, NewdeltaY, rotation =\
                LaserCut.FitPanelRotatable(self.lastX,self.lastY,
                                           lengthX,lengthY,
                                           self.deltaY,minX,minY,maxX,maxY)
        else:
            fitP, currentX, currentY, lengthX, lengthY, NewdeltaY, rotation =\
                LaserCut.FitPanelNonRotatable(self.lastX,self.lastY,
                                              lengthX,lengthY,
                                              self.deltaY,minX,minY,maxX,maxY)
        
        if not fitP:
            #debug("*** LaserCut.__AddCut(%s,...) failed"%(self))
            return False
        #debug("*** LaserCut.__AddCut(%s,...) currentX is %.4f, currentY is %.4f, lengthX is %.4f, lengthY is %.4f, NewdeltaY is %.4f, rotation is %f"%(self,currentX, currentY, lengthX, lengthY, NewdeltaY, rotation))
        obj = self.Document().addObject("Part::Feature",self.ObjName())
        obj.Shape = shape
        obj.ViewObject.Visibility = False
        panel = self.Document().addObject('TechDraw::DrawViewPart',self.ObjName()+"_View")
        self.page.addView(panel)
        panel.Source = obj
        panel.X = currentX+lengthX/2
        panel.Y = currentY+lengthY/2
        panel.Rotation = rotation
        panel.Direction = direction
        self.IncrObjNum()
        self.Document().recompute()
        self.lastX = currentX+lengthX+3.175
        self.lastY = currentY
        self.deltaY = NewdeltaY
        return True
    __Prefix = ""
    @classmethod
    def SetPrefix(cls,prefix):
        cls.__Prefix = prefix
    @classmethod
    def GetPrefix(cls):
        return cls.__Prefix
    def finish(self):
        #debug("*** LaserCut.finish(%s)"%(self))
        self.Document().recompute()
        sleep(500)
        TechDrawGui.exportPageAsSvg(self.page,
                                    os.path.join(os.path.dirname(__file__),
                                                 self.GetPrefix()+self.filename))
    @classmethod
    def Flush(cls):
        if cls.__currentSheet != None:
            cls.__currentSheet.finish()
            cls.__currentSheet = None
                    
            
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

class StyreneSSS_10824Cut(LaserCut):
    @property
    def SheetThick(self):
        return .080*25.4
    @property
    def SheetWidth(self):
        return 600
    @property
    def SheetLength(self):
        return 300
    @property
    def SheetTemplate(self):
        return os.path.join(os.path.dirname(__file__),"CutPanel300x600.svg")
    def __init__(self):
        self.Init()
        # remaining init...

class StyreneSSS_10224Cut(LaserCut):
    @property
    def SheetThick(self):
        return .020*25.4
    @property
    def SheetWidth(self):
        return 600
    @property
    def SheetLength(self):
        return 300
    @property
    def SheetTemplate(self):
        return os.path.join(os.path.dirname(__file__),"CutPanel300x600.svg")
    def __init__(self):
        self.Init()
        # remaining init...

