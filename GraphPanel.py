"""Classes for adding sumlines to frames

This module contains a single class, GraphPanel, which plots two dimensional
data filled along a chosen axis.  This class was originally designed for giving
the summation of a matrix along a given axis, but there's not reason that it
couldn't be expanded for other purposes.

"""

import numpy as np

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
#import matplotlib.cm as cm

import wx

# FIXME:  This function is extremely brittle
def rebin(a,count):
    """A quick function to rebin an array

    This function takes an array and rebins it into a smaller array.
    Note that, if the length of the array isn't divisible by the binning
    factor, the end of the array will be truncated.  This is probably
    not a sane default, but I don't have any better ideas.

    Keyword arguments:
    a -- The numpy array to be rebinned.
    count -- The number of bins to be combined.  For instance, if the array
             has a length of 100 and the count is 4, the return value
             will have a length of 25

    """

    return np.array([a[i:i+count].mean() for i in range(0,len(a),count)])

class GraphPanel(wx.Panel):
    """This class creates a panel that displays a filled plot. """

    
    HORIZONTAL = 0 
    INVERTED = 1
    VERTICAL = 2
    def __init__(self,parent,fig,res,orientation):
        """Create a new panel for plotting.

        Keyword Arguments:
        parent -- the panel in which the new one is to be displayed
        fig -- a tuple representing the relative dimensions of the panel
        res -- the number of pixels per part of the fig tuple.
        orientation -- the rotation of the image

        fig and res combine to produce the total size, in pixels, of the
        panel.  For instance, if fig=(2,8) and res=64, the final panel
        has a size of (128,512)

        The orientation can be one of HORIZONTAL, VERTICAL, or INVERTED,
        as defined as constants in the class definition. Horitzontal uses
        the standard x and y axes, and is best for putting above a 2d image.
        VERTICAL swaps the x and y axes and is best for going to the right
        of an image.  INVERTED plots with x and -y, and is best below the image.

        """
        wx.Panel.__init__(self,parent)
        self.Bind(wx.EVT_PAINT,self.__OnPaint)
        #The actual figure for plotting
        self.figure = Figure(figsize=fig,dpi=res)
        #The space where th figure is drawn
        self.canvas = FigureCanvas(self,-1,self.figure)
        #The rotation of the figure.
        self.orientation=orientation

    def SetPlot(self,x,y):
        """Set the x and y coordinates of the data to be plotted."""
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        #We rebin the data in steps of four to smooth out the dead PMTs
        #If all of the PMTs have been fixed, this step could be taken out.
        if self.orientation==self.INVERTED:
            self.axes.fill_between(x,y)
            self.SetPos([0,0.1,1,0.9])
            self.axes.set_xlim((0,np.max(x)))
            #Reverse the order of the limits to get an inverted graph
            self.axes.set_ylim((np.max(y),0))
        elif self.orientation==self.HORIZONTAL:
            self.axes.fill_between(x,y)
            self.SetPos([0.1,0.1,0.9,0.9])
            self.axes.set_xlim((0,np.max(x)))
            self.axes.set_ylim((0,np.max(y)))
        else:
            #Notice that we now fill along the x axis
            self.axes.fill_betweenx(x,y)
            self.SetPos([0.2,0,0.8,1])
            self.axes.set_xlim((np.max(x),0))
            self.axes.set_ylim((0,np.max(y)))

        self.axes.autoscale_view(True,True,True)
        self.Refresh()

#     def SetYLim(self,range):
#         self.axes.set_ylim(range)

#     def SetXLim(self,range):
#         self.axes.set_xlim(range)


    def SetPos(self,pos):
        """Set the position of the graph within the panel.

        This function take a four element array which marks the far
        corners of the graph.  The coordinates are given as a fraction
        of the size of the panel.  For instance, pos=[0,0.3333,1,0.6666]
        would produce a graph that stretches across the panel in the x
        direction, but only uses the middle third in the y direction.
        You will probably need to play with these values in order to be 
        able to view the values of the axes on the plot.

        """
        self.axes.set_position(pos)

    def __OnPaint(self,event):
        """An event handler to tell the canvas to draw
        when the panel is redrawn."""
        self.canvas.draw()
        event.Skip()
