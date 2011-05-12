"""Convenience classes for plotting data

This module contains a single class, GraphFrame, which is used for easily
plotting two dimensional data.  If other such convenience classes are
ever to be written, they should be put into this module.

"""

import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

class GraphFrame(wx.Frame):
    """
    This class merges wxWidgets and matplotlib to produce an 
    independent frame which can display a two dimensional
    plot fo arbitrary data.

    """
    ID_COPY = 500
    def __init__(self,parent=None,title=""):
        """Creates a new frame for displaying graphs

        Keyword arguments:
        parent -- the parent frame of the new frame
        title -- the title for the frame.  This is not the title
                 for the graph.

        """
        wx.Frame.__init__(self,parent,wx.ID_ANY,title)

        self.panel = wx.Panel(self)
        self.panel.Bind(wx.EVT_PAINT,self.__PanelPaint)

        menubar = wx.MenuBar()
        editmenu = wx.Menu()
        editmenu.Append(self.ID_COPY,"&Copy\tCtrl-C"," Copy image to the clipboard")
        self.Connect(self.ID_COPY,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnCopy)
        menubar.Append(editmenu,"&Edit")
        self.SetMenuBar(menubar)
        

        #First, make the plotting figure.
        self.figure = Figure()
        #Then give the figure somewhere to display.
        self.canvas = FigureCanvas(self.panel,-1,self.figure)
        #Finally, make a Toolbar to adjust the canvas at runtime.
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()

        sizer = wx.GridBagSizer()
        sizer.Add(self.canvas,pos=wx.GBPosition(1,0))
        sizer.Add(self.toolbar,pos=wx.GBPosition(0,0))
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)

    def __PanelPaint(self,event):
        """Event handler to tell the canvas to 
        redraw when the window is drawn."""
        self.canvas.draw()
        event.Skip()

    def OnCopy(self,event):
        """Copies the image of the graph to the system Clipboard"""
        if wx.TheClipboard.Open():
            print(self.canvas.GetSize())
            w,h=self.canvas.GetSize()
            bitmap = wx.EmptyBitmap(x,y,24)
            memdc = wx.MemoryDC(bitmap)
            self.figure.canvas.draw(memdc)
            wx.TheClipboard.Clear()
            wx.TheClipboard.SetData(wx.BitmapDataObject(bitmap))
            wx.TheClipboard.Close()

    def plot(self,x,y,range=None,xerr=None,yerr=None):
        """Plots 2D data in the frame

        This method is the main workhorse of the class.  It plots
        a line representing the x and y data, with optional errorbars.

        Keyword arguments:
        x -- numpy array of x coordinates
        y -- numpy array of y corrdinates
        range -- either a tuple with the minimum and maximum y values,
                 or None for autoscaling
        xerr -- numpy array of the errors in the x direction
        yerr -- numpy array of errors in the y direction

        """
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        axes.errorbar(x,y,xerr=xerr,yerr=yerr)
        if range==None:
            axes.autoscale_view(True,True,True)
        else:
            (vmin,vmax)=range
            axes.set_ylim(vmin,vmax)
            axes.autoscale_view(True,True,False)
        self.Show()
