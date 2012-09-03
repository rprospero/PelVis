"""This module contains classes which help in displaying 2D data

This module currently contains one class: ImagePanel.  The imagePanel
takes a 2D array and displays it as a color plot.

"""

import numpy as np

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import matplotlib.cm as cm

import wx


if __name__ == "__main__":
    print "Hello World";

class ImagePanel(wx.Panel):
    """This class displays 2D data as a color plot"""
    def __init__(self,parent,posFunction=None,setMin=None,setMax=None):
        """This creates an ImagePanel
        
        Keyword arguments:
        parent -- The container which will hold the panel
        posFunction -- function to be updated with mouse position
        setMin -- function to be called on left click
        setMax -- function to be called on right click

        """
        wx.Panel.__init__(self,parent)
        self.Bind(wx.EVT_PAINT,self.__OnPaint)
        self.posFunction = posFunction#Function to call on mouse movement
        self.setMin = setMin#Function to call on right click
        self.setMax = setMax#Function to call on left click

        #The figure which holds the graph
        self.figure = Figure(figsize=(1,1),dpi=512)
        #The object where the graph is drawn
        self.canvas = FigureCanvas(self,-1,self.figure)
        self.canvas.Bind(wx.EVT_MOTION,self.__OnMouseMove)
        self.canvas.Bind(wx.EVT_LEFT_UP,self.__OnMouseLeft)
        self.canvas.Bind(wx.EVT_RIGHT_UP,self.__OnMouseRight)
        
        self.cmap = cm.jet#The color map for the graph

        #Known file formats for saving images
        self.handlers={u"BMP":wx.BITMAP_TYPE_BMP,
                        u"JPG":wx.BITMAP_TYPE_JPEG,
                        u"PNG":wx.BITMAP_TYPE_PNG,
                        u"PCX":wx.BITMAP_TYPE_PCX,
                        u"PNM":wx.BITMAP_TYPE_PNM,
                        u"TIF":wx.BITMAP_TYPE_TIF}

    def __OnPaint(self,event):
        """Event handler to redraw graph when panel is redrawn."""
        self.canvas.draw()
        event.Skip()

    def __OnMouseMove(self,event):
        """Event handler when the mouse moves over the graph"""
        (x,y) = event.GetPosition()
        if self.posFunction is None: return
        self.posFunction(x,y)

    def __OnMouseLeft(self,event):
        """Event handler for left clicking on the graph."""
        (x,y) = event.GetPosition()
        if self.setMin is None: 
            None
        else:
            self.setMin(x,y)
        event.Skip()

    def __OnMouseRight(self,event):
        """Event handler for right clicking on the graph."""
        (x,y) = event.GetPosition()
        if self.setMax is None: 
            None
        else:
            self.setMax(x,y)
        event.Skip()

    def update(self,data,vmin=10,vmax=20):
        """Change the dataset for the graph

        Keyword arguments:
        data -- 2D numpy array
        vmin -- floor value for graphing
        vmax -- ceiling value for graphing

        """
        self.data=data
        self.figure.clear()
        self.figure.add_axes((0,0,1,1),autoscale_on=True,frameon=False,yticks=[0,1],xticks=[0,1])
        self.figure.get_axes()[-1].get_xaxis().set_visible(False)
        self.figure.get_axes()[-1].get_yaxis().set_visible(False)
        self.figure.get_axes()[-1].imshow(data,cmap=self.cmap,vmin=vmin,vmax=vmax,aspect="auto")
        self.figure.canvas.draw()
        self.Refresh()

    def saveImage(self,path):
        """Saves the graph to an image file"""
        bitmap = wx.EmptyBitmap(512,512,24)
        memdc = wx.MemoryDC(bitmap)
        self.figure.canvas.draw(memdc)
        image = wx.Bitmap.ConvertToImage(bitmap)
        image.SaveFile(path,self.handlers[path[-3:].encode('ascii')])

    def copyToClipboard(self):
        """Copies the image of the graph to the system Clipboard."""
        if wx.TheClipboard.Open():
            bitmap = wx.EmptyBitmap(512,512,24)
            memdc = wx.MemoryDC(bitmap)
            self.figure.canvas.draw(memdc)
            wx.TheClipboard.Clear()
            wx.TheClipboard.SetData(wx.BitmapDataObject(bitmap))
            wx.TheClipboard.Close()
