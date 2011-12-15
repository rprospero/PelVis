"""Classes for handling color spectra

This module implements a series of classes for handling the different color
spectra produced by matplot lib.  The basic class is ColorBarPanel, which
simply displays a given color map.  ActionColorbar subclasses ColorBarPanel
to add simple click response abilities.  Finally, ColorBarPicker gives the
user the ability to select any of the color maps that matplotlib is aware of.
Note that ColorBarPicker takes time to render when it first loads, so care
should be taken not to create one unless it's necessary and then to keep
that same on for as long as possible.

"""

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import Normalize
import matplotlib.cm as cm

import wx

class ColorBarPanel(wx.Panel):
    """Panel to display a ColorBar in a wxWidgets container."""
    def __init__(self,parent,cmap,fig=(1,10),
                 res=64,orientation='vertical',
                 size=[0,0.025,0.6,0.95]):
        """Creates a ColorBarPanel.

        Keyword arguments:
        parent -- container which holds the panel.
        cmap -- the color map to display in the color bar.
                This should be a matplotlib cmap object
        fig -- the relative width to height of the color bar
        res -- the number of pixels per unit in fig
        orientation -- the rotation of the color bar
        size -- the position of the color bar in the panel

        res and size combine to produce the actual size of the
        panel in pixels.  For instance, with fig=(1,10) and res=64,
        the panel will be 64 pixels wide and 640 pixels tall.

        size is a four element array which marks the far
        corners of the graph.  The coordinates are given as a fraction
        of the size of the panel.  For instance, pos=[0,0.3333,1,0.6666]
        would produce a graph that stretches across the panel in the x
        direction, but only uses the middle third in the y direction.
        The default value should allow the axes to be seen.

        """

        wx.Panel.__init__(self,parent)
        self.Bind(wx.EVT_PAINT,self.__OnPaint)

        self.figure = Figure(figsize=fig,dpi=res)#the actual plot
        #the object to display the plot
        self.canvas = FigureCanvas(self,-1,self.figure)
        #the direction of the color bar
        self.orientation=orientation
        #the color map to use
        self.cmap=cmap
        self.vmin=0 #The minimum value on the color bar
        self.vmax=18 #The maximum value on the color bar
        self.size=size #The position of the color bar in the frame
        self.update()

    def setRange(self,vmin,vmax):
        """Set the range for the axes on the colorbar."""
        self.vmin=vmin
        self.vmax=vmax

    def setCmap(self,cmap):
        """Pick the colormap to display."""
        self.cmap = cmap

    def update(self):
        """Reacts to any changes in the objects members."""
        axes = self.figure.add_axes(self.size)
        norm = Normalize(vmin=self.vmin,vmax=self.vmax)
        colorbar = ColorbarBase(axes,cmap=self.cmap,norm=norm,
                                orientation=self.orientation)
        self.Refresh()
        
    def __OnPaint(self,event):
        """An event handler to update the graph when the panel is redrawn."""
        self.canvas.draw()
        event.Skip()

class ActionColorbar(ColorBarPanel):
    """A simplistic colorbar button

    This class displays a colormap and returns the name of its colormap
    to a given function when clicked on by the user.

    """
    def __init__(self,parent,cmap,command):
        """Creates an ActionColorbar

        Keyword arguments:
        parent -- the container to hold the panel.
        cmap -- a string naming a colormap.
        command -- the function to run when the colormap is clicked.

        """
        #title attribute is needed by update, which is called by init
        self.title=cmap#The title of the colormap
        ColorBarPanel.__init__(self,parent,cm.get_cmap(cmap),fig=(5,1),orientation='horizontal',size=[0,0,1,0.6])
        self.comm = command#The command to run on clicks
        self.canvas.Bind(wx.EVT_LEFT_UP,self.__OnClick)

    def update(self):
        """Reacts to any changes in the objects members."""
        axes = self.figure.add_axes(self.size,title=self.title)
        norm = Normalize(vmin=self.vmin,vmax=self.vmax)
        colorbar = ColorbarBase(axes,cmap=self.cmap,norm=norm,
                                orientation=self.orientation)
        self.Refresh()

    def __OnClick(self,event):
        """Event handler to call self.comm when the panel is clicked."""
        self.comm(self.cmap)
        event.Skip()

class ColorMapPicker(wx.Frame):
    """A window for selecting a color map"""
    def __init__(self,parent,command):
        """Creates a ColorMapPicker

        Keyword arguments:
        parent -- parent of this frame or None
        command -- function to be called on the chosen colormap name

        """
        wx.Frame.__init__(self,parent,wx.ID_ANY,"Maps",size=(345,355))
        scroll = wx.ScrolledWindow(self,-1)
        sizer = wx.BoxSizer(wx.VERTICAL)
        keys = cm.datad.keys()
        #Iterate through all of the colormap names
        for key in keys[:]:
            sizer.Add(ActionColorbar(scroll,key,command))
            scroll.SetScrollbars(0,64,0,64)
        sizer.SetSizeHints(scroll)
        scroll.SetSizer(sizer)
        self.Bind(wx.EVT_CLOSE,self.__OnClose)

    def __OnClose(self,event):
        """Event handler for closing the window

        Since the window takes so long to build and render, we
        don't want to be forces to make a new one each time it's
        closed, so we merely hide it when the user closes it."""
        self.Hide()



if __name__ == '__main__':
    def printcmap(cmap):
        print(cmap)

    app=wx.PySimpleApp()
    frame = ColorMapPicker(None,printcmap)
    frame.Show()
    app.MainLoop()
