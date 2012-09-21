"""A GUI for handling polarization data generated by a PAPA detector.

This program was written to help with analyzing polarization data produced
by the PAPA detector.  The general workflow is:
1)Load Neutron Data
2)Subtract Background
3)Select Region of Interest
4)Plot Spectrum data

The primary class is PelvisFrame, which controls the whole program.
PelvisFrame contains a PositionPanel, to examine single pixels, and
a PelvisOptionPanel, which accepts user parameters.

"""

import __future__

from reader import PelFile
from ImagePanel import ImagePanel
from GraphPanel import GraphPanel
from colorbarpanel import ColorBarPanel, ColorMapPicker
from monfile import MonFile
from SpectrumDialog import SpectrumDialog

from tempfile import TemporaryFile

import math

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.cm as cm

import wx

class PositionPanel(wx.Panel):
    """A panel with pixel information

    The intent of this panel is to provide information about
    single pixels of detector data via cursor position.  It
    also provides aggregate information over the region of
    interest.

    """
    def __init__(self,parent):
        """Create a PositionPanel"""
        wx.Panel.__init__(self,parent)
        sizer=wx.GridBagSizer(3,2)
        sizer.Add(wx.StaticText(self,-1,"X:"),pos=wx.GBPosition(0,0))
        self.x = wx.TextCtrl(self,-1,"")
        sizer.Add(self.x,pos=wx.GBPosition(0,1))
        sizer.Add(wx.StaticText(self,-1,"Y:"),pos=wx.GBPosition(1,0))
        self.y = wx.TextCtrl(self,-1,"")
        sizer.Add(self.y,pos=wx.GBPosition(1,1))
        sizer.Add(wx.StaticText(self,-1,"Z:"),pos=wx.GBPosition(2,0))
        self.intensity = wx.TextCtrl(self,-1,"")
        sizer.Add(self.intensity,pos=wx.GBPosition(2,1))
        self.integrate = wx.TextCtrl(self,-1,"")
        sizer.Add(wx.StaticText(self,-1,"ROI:"),pos=wx.GBPosition(3,0))
        sizer.Add(self.integrate,pos=wx.GBPosition(3,1))

        #Set the starting region of interest
        self.minX = 0
        self.minY = 0
        self.maxX = 16
        self.maxY = 128

        self.x.SetEditable(False)
        self.y.SetEditable(False)
        self.intensity.SetEditable(False)
        self.data = None #A 2D numpy array of the data being examined.

        self.SetAutoLayout(True)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        self.Layout()
    def set(self,x,y):
        """Updates the position being examined"""
        self.x.SetValue(str(x))
        self.y.SetValue(str(y))
        if self.data is None:
            return
        self.intensity.SetValue(str(self.data[y,x]))
    def setData(self,data):
        """Updates the data being examined"""
        self.data=data
    def setRange(self,minX,minY,maxX,maxY):
        """Updates the region of interest for integration"""
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY
        self.updateIntegration()
    def updateIntegration(self):
        """Calculates the sum of the data over the region of interest"""
        self.integrate.SetValue(
            str(np.sum(self.data[self.minY:self.maxY,self.minX:self.maxX])))

class PelvisOptionPanel(wx.Panel):
    """A panel for user parameters

    The panel gets it's parameters and appearance from the built in
    DEFAULTS variable.  This was designed to allow the easy addition
    of more parameters in the future.

    """
    #Each parameter is a tuple
    #0 - variable name
    #1 - position in list
    #2 - label
    #3 - default value
    DEFAULTS = [("lambdaMax",0,"Maximum Wavelength","20"),
                ("lambdaMin",10,"Minimum Wavelength","0"),
                ("intMax",20,"Maximum Intensity",""),
                ("intMin",30,"Minimum Intensity",""),
                ("xMin",40,"Minimun X","0"),
                ("xMax",50,"Maximum X","16"),
                ("yMin",60,"Minimun Y","0"),
                ("yMax",70,"Maximum Y","128")]

    def __init__(self,parent):
        """Creates a PelvisOptionPanel"""
        wx.Panel.__init__(self,parent)
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        self.options={}#member which holds the created text controls

        self.DEFAULTS.sort(lambda x,y: x[1]-y[1])
        for option in self.DEFAULTS:
            (key,_,title,val) = option
            sizer.Add(wx.StaticText(self,-1,title))
            self.options[key] = wx.TextCtrl(self,-1,val)
            sizer.Add(self.options[key])
            

        self.SetAutoLayout(True)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        self.Layout()

    def getLambdaRange(self):
        """Gives a tuple with the minimum and maximum wavelength indices"""
        try:
            lmin = int(float(self.options["lambdaMin"].GetValue())*10)
        except ValueError:
            lmin = 0
        try:
            lmax = int(float(self.options["lambdaMax"].GetValue())*10)
        except ValueError:
            lmax = 200 
        return (lmin,lmax)

    def setLambdaRange(self,min,max):
        """Set the minimum and maximum wavelengths"""
        self.options["lambdaMin"].SetValue(str(min))
        self.options["lambdaMax"].SetValue(str(max))

    def getIntensityRange(self):
        """Return a tuple with the floor and ceilling for intensity

        If a value isn't specified, or is not a number, None is returned
        for that part of the range.

        """
        try:
            vMin = float(self.options["intMin"].GetValue())
        except ValueError:
            vMin = None
        try:
            vMax = float(self.options["intMax"].GetValue())
        except ValueError:
            vMax = None
        return (vMin,vMax)

    def getRoi(self):
        """Returns a 4-tuple with the region of interest

        Returns (xmin,xmax,ymin,ymax).  Minimum values, if
        unspecified, are set to zero.  Maximum values, if
        unspecified, are set to 512.

        """
        try:
            xMin = int(self.options["xMin"].GetValue())
        except ValueError:
            xMin = 0
        try:
            xMax = int(self.options["xMax"].GetValue())
        except ValueError:
            xMax = 512
        try:
            yMin = int(self.options["yMin"].GetValue())
        except ValueError:
            yMin = 0
        try:
            yMax = int(self.options["yMax"].GetValue())
        except ValueError:
            yMax = 512
        return (xMin,xMax,yMin,yMax)

    def setPosMin(self,x,y):
        """Takes the x and y coordinates for the NW corner of the ROI."""
        self.options["xMin"].SetValue(str(x))
        self.options["yMin"].SetValue(str(y))

    def setPosMax(self,x,y):
        """Takes the x and y coordinates for the SE corner of the ROI."""
        self.options["xMax"].SetValue(str(x))
        self.options["yMax"].SetValue(str(y))


class PelvisFrame(wx.Frame):
    """The main application window for PELvis"""

    #Menu ID constants
    ID_OPEN = 100
    ID_OPENTWO = 110
    ID_SAVE = 130
    ID_SPECTRUM=140
    ID_IMAGE_ARRAY=160
    ID_EXIT = 190

    ID_GREY = 200
    ID_HUEVAL = 220
    ID_SPECTRAL = 230
    ID_PICKER = 290
    ID_POLAR = 300
    ID_FLIPPING = 310
    ID_SPIN_UP = 320
    ID_SPIN_DOWN = 330

    ID_FLAT = 420
    ID_FAKEFLAT = 430
    ID_ROD = 440
    ID_EXPORT_ROI = 450
    ID_IMPORT_ROI = 460

    ID_COPY = 500

    def __init__(self,Yield):
        """Create a PELvis frame

        Keyword arguments:
        Yield -- A function to give control back to the main event loop

        """
        wx.Frame.__init__(self,None,wx.ID_ANY,"PEL Visualizer")
        self.data = PelFile()
        self.Yield = Yield
        self.mask = np.ones((128,16),dtype=np.bool)

        #Create items in the frame
        self.yPanel = GraphPanel(self,(2,8),64,GraphPanel.VERTICAL)
        self.xPanel = GraphPanel(self,(8,2),64,GraphPanel.INVERTED)
        self.colorbar = ColorBarPanel(self,cm.jet)
        self.opPanel = PelvisOptionPanel(self)
        self.posPanel = PositionPanel(self)
        self.imPanel = ImagePanel(self,self.posPanel.set,
                                  self.opPanel.setPosMin,self.opPanel.setPosMax)
        self.specDlg = SpectrumDialog(self)

        self.cmp = None #color map
        self.imageSaveDialog=wx.FileDialog(self,"Choose graphics file",wildcard="Portable Network Graphic (png)|*.PNG|Windows Bitmap (bmp)|*.BMP|Joint Photographic Experts Group (jpg)|*.JPG|Portable Network Monocrome (pnm)|*.PNM|Tagged Image File Format (tif)|*.TIF|Archaic, useless format (pcx)|*.PCX",style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)

        self.update = self.updateSingle#update the image
        self.updateData = self.updateSingleData#update the data in the image

        #Create the menu
        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        editmenu = wx.Menu()
        scalemenu = wx.Menu()
        analysismenu = wx.Menu()
        noisemenu = wx.Menu()

        #populate the menu
        filemenu.Append(self.ID_OPEN,"&Open\tCtrl-O"," Open a PEL file")
        filemenu.Append(self.ID_OPENTWO,"&Polarized Set"," Open two PEL files")
        filemenu.Append(self.ID_SAVE,"&Save\tCtrl-S"," Save an image file")
        filemenu.Append(self.ID_SPECTRUM,"Spectrum"," View the TOF spectrum")
        filemenu.Append(self.ID_IMAGE_ARRAY,"&Export Images..."," Save a series of TOF snapshots")
        filemenu.Append(self.ID_EXIT,"&Quit\tCtrl-Q"," Quit")

        editmenu.Append(self.ID_COPY,"&Copy\tCtrl-c","Copy the current image to the clipboard")

        scalemenu.Append(self.ID_GREY,"Greyscale\tCtrl-G","Monochrome images")
        scalemenu.Append(self.ID_HUEVAL,"Hue and Value\tCtrl-H","Scaled Rainbow Images")
        scalemenu.Append(self.ID_SPECTRAL,"spectral","Uses spectrum of light")
        scalemenu.Append(self.ID_PICKER,"Map Picker..."," Select from the full list of colormaps")

        analysismenu.Append(self.ID_POLAR,"Check Polarization\tCtrl-P","2d plot of polarization data")
        analysismenu.Append(self.ID_FLIPPING,"Check Flipping Ratio\tCtrl-F","2d plot of  spin up over spin down")
        analysismenu.Append(self.ID_SPIN_UP,"View Spin Up State\tCtrl-U","2d plot of  spin up")
        analysismenu.Append(self.ID_SPIN_DOWN,"View Spin Down State\tCtrl-D","2d plot of  spin down")

        noisemenu.Append(self.ID_FLAT,"&Load Flat"," Load a blank run for background subtraction")
        noisemenu.Append(self.ID_FAKEFLAT,"Si&mulate Flat"," Drop out background within the same image")
        noisemenu.Append(self.ID_ROD,"Region of &Disinterest"," Drop out background within the same image")
        noisemenu.Append(self.ID_EXPORT_ROI,"Export ROI"," Export a binary file corresponding to where the data is above the minimum intensity.")
        noisemenu.Append(self.ID_IMPORT_ROI,"Import ROI"," Add another exclusion mask.")


        #Bind events to the menu
        self.Connect(self.ID_EXIT,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnExit)
        self.Connect(self.ID_OPEN,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnOpen)
        self.Connect(self.ID_OPENTWO,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnOpenSet)
        self.Connect(self.ID_SAVE,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnSave)
        self.Connect(self.ID_SPECTRUM,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnSpectrum)
        self.Connect(self.ID_IMAGE_ARRAY,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnImageArray)
        self.Connect(self.ID_GREY,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnGrey)
        self.Connect(self.ID_HUEVAL,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnHueVal)
        self.Connect(self.ID_SPECTRAL,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnSpectral)
        self.Connect(self.ID_PICKER,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnPicker)
        self.Connect(self.ID_POLAR,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnPolar)
        self.Connect(self.ID_FLIPPING,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnFlipping)
        self.Connect(self.ID_SPIN_UP,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnAnalysisSpinUp)
        self.Connect(self.ID_SPIN_DOWN,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnAnalysisSpinDown)

        self.Connect(self.ID_FLAT,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnFlat)
        self.Connect(self.ID_FAKEFLAT,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnFakeFlat)
        self.Connect(self.ID_ROD,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnROD)
        self.Connect(self.ID_EXPORT_ROI,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnExportROI)
        self.Connect(self.ID_IMPORT_ROI,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnImportROI)
        self.Connect(self.ID_COPY,-1,wx.wxEVT_COMMAND_MENU_SELECTED,self.OnCopy)

        menubar.Append(filemenu,"&File")
        menubar.Append(editmenu,"&Edit")
        menubar.Append(scalemenu,"&Color")
        menubar.Append(analysismenu,"&Analysis")
        menubar.Append(noisemenu,"&Noise")
        self.SetMenuBar(menubar)

        #arrange window
        sizer = wx.GridBagSizer()
        sizer.Add(self.colorbar,pos=wx.GBPosition(0,9),span=wx.GBSpan(9,1))
        sizer.Add(self.imPanel,pos=wx.GBPosition(0,1),span=wx.GBSpan(8,8))
        sizer.Add(self.yPanel,pos=wx.GBPosition(0,0),span=wx.GBSpan(8,1))
        sizer.Add(self.xPanel,pos=wx.GBPosition(8,1),span=wx.GBSpan(1,8))
        sizer.Add(self.opPanel,pos=wx.GBPosition(0,10),span=wx.GBSpan(8,1),flag=wx.EXPAND)
        sizer.Add(self.posPanel,pos=wx.GBPosition(8,0),flag=wx.EXPAND)
        self.progress = wx.Gauge(self,range=1000)
        sizer.Add(self.progress,pos=wx.GBPosition(9,0),span=wx.GBSpan(1,11),flag=wx.EXPAND)

        updateButton = wx.Button(self,-1,"Update")
        updateButton.Bind(wx.EVT_BUTTON,self.OnUpdateButton)
        sizer.Add(updateButton,flag=wx.EXPAND,pos=wx.GBPosition(8,10))

        self.data = self.makePel()
        self.flatrun = None#background data
        
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        self.Show(True)

    def makePel(self):
        """Create a blank Pel object for loading detector data"""
        data = PelFile()
        def statusfunc(x):
            self.progress.SetValue(x)
            self.Yield()
        data.statusfunc = statusfunc
        return data

    def loadPel(self,message):
        """Load a .pel file and its monitor data.

        Keyword arguments:
        message -- The title for the load file dialog.

        """
        dlg=wx.FileDialog(self,message,wildcard="He3 data|*neutron_event.dat|Preformatted Histograms|*.npy",style=wx.FD_OPEN)
        if dlg.ShowModal()==wx.ID_OK:
#            self.SetCursor(wx.CURSOR_WAIT)
            path = dlg.GetPath()
            if path[-3:] == "dat":
                data = self.makePel()
                data.readfileimage(path)
            elif path[-3:] == "npy":
                data = np.load(path)
#            self.SetCursor(wx.CURSOR_ARROW)
        else:
            return (None,None)
        mon = MonFile(path[:-17]+"bmon_histo.dat")
        return (data,mon)

    def OnImageArray(self,event):
        """Exports the 2d detector image by wavelength"""
        dlg = self.imageSaveDialog
        if dlg.ShowModal()==wx.ID_OK:
            path=dlg.GetPath()
            ext = path[-4:]
            path = path[:-4]
            (lmin,lmax) = self.opPanel.getLambdaRange()
            for i in range(lmin,lmax):
                file=path+("%03i"%i)+ext
                self.opPanel.setLambdaRange(0.1*i,0.1*(i+1))
                self.updateData()
                self.imPanel.saveImage(file)
                self.progress.SetValue(1000*(i-lmin)/(lmax-lmin))
                self.Yield()
            self.opPanel.setLambdaRange(lmin*0.1,lmax*0.1)
            self.updateData()
            self.progress.SetValue(0)

    def loadNormPel(self,message):
        """Load a .pel file, normalize it by monitor, and subtract background"""
        (data,mon) = self.loadPel(message)
        if isinstance(data,PelFile):
            data = np.asarray(data.make3d(),np.float32)
        if mon is None:
            return (data,1)
        if self.flatrun != None:
            flatrun = np.load(self.flatrun)
            self.flatrun.seek(0)
            flatrun *= mon.time
            data -= flatrun
        spec = mon.spec
        data /= np.sum(spec)
        return (data,np.sum(mon.spec))
                
#    def getLambdaRange(self):
#        try:
#            lmin = int(float(self.lambdaMin.GetValue())*10)
#        except ValueError:
#            lmin = 0
#        try:
#            lmax = int(float(self.lambdaMax.GetValue())*10)
#        except ValueError:
#            lmax = 200 
#        return (lmin,lmax)

    def updateSingleData(self,event=None):
        """Update changes in wavelength on a single file"""
        print("Make 2d")
        (lmin,lmax) = self.opPanel.getLambdaRange()
        self.flatdata = np.sum(self.data[:,:,lmin:lmax],2)
        self.update()

    def updateDataFlip(self,event=None):
        """Update changes in wavelength for flipping ratios"""
        (lmin,lmax) = self.opPanel.getLambdaRange()
        (u3d,d3d)=self.data
        u = np.sum(u3d[:,:,lmin:lmax],2)
        d = np.sum(d3d[:,:,lmin:lmax],2)
        self.flatdata = u/(d+1e-6)
        self.update()

    def updateDataPolar(self,event=None):
        """Update changes in wavelength for polarizations"""
        (lmin,lmax) = self.opPanel.getLambdaRange()
        (u3d,d3d)=self.data
        u = np.sum(u3d[:,:,lmin:lmax],2)
        d = np.sum(d3d[:,:,lmin:lmax],2)
        self.flatdata = (u-d)/(u+d+1e-6)
        self.update()

    def updateDataUp(self,event=None):
        """Update changes in wavelength for the spin up state"""
        (lmin,lmax) = self.opPanel.getLambdaRange()
        (u3d,_)=self.data
        self.flatdata = np.sum(u3d[:,:,lmin:lmax],2)
        self.update()

    def updateDataDown(self,event=None):
        """Update changes in wavelength for the spin down state"""
        (lmin,lmax) = self.opPanel.getLambdaRange()
        (_,d3d)=self.data
        self.flatdata = np.sum(d3d[:,:,lmin:lmax],2)
        self.update()

    def updateSingle(self,event=None):
        """Update the 2D data for the region of interest and intensity"""
        (vMin,vMax) = self.opPanel.getIntensityRange()
        (xMin,xMax,yMin,yMax) = self.opPanel.getRoi()
        data = self.flatdata
        self.posPanel.data = data
        self.posPanel.setRange(xMin,yMin,xMax,yMax)
        x=np.arange(128,0,-1)
        y=np.sum(data[:,xMin:xMax],axis=1)
        self.yPanel.SetPlot(x,y)
        #handle the x-plot
        x=np.arange(0,16,1)
        y=np.sum(data[yMin:yMax,:],axis=0)
        self.xPanel.SetPlot(x,y)
        self.imPanel.update(self.flatdata,vMin,vMax)
        if vMin is None:
            vMin = np.min(data)
        if vMax is None:
            vMax = np.max(data)
        self.colorbar.setRange(vMin,vMax)
        self.colorbar.update()

    def OnUpdateButton(self,event):
        """Refresh the data when the user pushes the "Update" button"""
        #This function is needed for wxWidgets to allow
        #for dynamically changing the bound function
        self.updateData(event)

    def OnOpen(self,event):
        """Load a single .pel file for display"""
        data,scale = self.loadNormPel("Choose the Pel File to Open")
        if data is None:
            return
        self.data = data
        self.scale = scale
        self.progress.SetValue(0)
        self.specDlg.setMode("up")
        self.updateData = self.updateSingleData
        self.update = self.updateSingle
        self.updateData()

    def OnOpenSet(self,event):
        """Load a spin flip measurement for display"""
        if self.loadUpAndDown():
            self.OnPolar(event)

    def OnFlat(self,event):
        """Load a blank run for background subtraction"""
        (data,mon) = self.loadPel("Choose a Blank Run")
        if data == None:
            return
        if isinstance(data,PelFile):
            flatrun = data.make3d()
        elif isinstance(data,np.ndarray):
            flatrun = data
        flatrun = np.sum(flatrun,axis=2)
        flatrun /= 200
        flatrun /= float(mon.time)
        flatrun = np.expand_dims(flatrun,2)
        self.flatrun = TemporaryFile()
        np.save(self.flatrun,flatrun)
        self.flatrun.seek(0)
        self.progress.SetValue(0)

    def OnFakeFlat(self,event):
        """Create a fake background run from outside the region of interest."""
        (xMin,xMax,yMin,yMax)=self.opPanel.getRoi()
        totarea = 512*512
        centarea = (yMax-yMin)*(xMax-xMin)
        backgroundarea = totarea-centarea
        if type(self.data) is tuple:
            (u,d)=self.data

            totu = np.sum(u)
            totd = np.sum(d)
            centu = np.sum(u[yMin:yMax,xMin:xMax,:])
            centd = np.sum(d[yMin:yMax,xMin:xMax,:])

            backgroundu = totu-centu
            backgroundd = totd-centd
            backgroundrateu = backgroundu/backgroundarea
            backgroundrated = backgroundd/backgroundarea
            backgroundrateu /= 201 #normalize against the wavelengths
            backgroundrated /= 201 #normalize against the wavelengths
            ###Stupid Memory Errors
            del self.data
            u -= backgroundrateu
            d -= backgroundrated
            ###
            self.data=(u,d)
        else:
            d=self.data
            tot = np.sum(d)
            cent = np.sum(d[yMin:yMax,xMin:xMax,:])
            background = tot-cent
            backgroundrate = background/backgroundarea
            backgroundrate /= 201 #normalize against the wavelengths
            self.data-=backgroundrate
        self.updateData()

    #Subtract out the region of disinterest
    def OnROD(self,event):
        """Take the region of interest as background noise"""
        (xMin,xMax,yMin,yMax)=self.opPanel.getRoi()
        area = (yMax-yMin)*(xMax-xMin)
        if type(self.data) is tuple:
            u,d=self.data
            del self.data
            totu = np.sum(np.sum(u[yMin:yMax,xMin:xMax,:],axis=0),axis=0)
            totd = np.sum(np.sum(d[yMin:yMax,xMin:xMax,:],axis=0),axis=0)
            totu /= area
            totd /= area
            u -= totu
            d -= totd
            self.data=(u,d)
        else:
            d=self.data
            totd = np.sum(np.sum(d[yMin:yMax,xMin:xMax,:],axis=0),axis=0)
            #totd = np.atleast_3d(totd)
            totd /= area
            print(totd.shape)
            print(self.data.shape)
            self.data -= totd
        self.updateData()

    def OnExportROI(self,event):
        """Save a file containing a map of where the current data
        image is greater than vmin"""
        vMin,_ = self.opPanel.getIntensityRange()
        mask = self.flatdata > vMin
        dlg = wx.FileDialog(self,
                            "Where to save the mask file?",
                            wildcard="Numpy dump (npy)|*.npy|Text (dat)|*.dat",
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal()==wx.ID_OK:
            path=dlg.GetPath()
            ext = path[-4:]
            if ext == ".dat":
                np.savetxt(path,mask,fmt="%d")
            else:
                np.save(path,mask)

    def OnImportROI(self,event):
        """Adds another mask to the current system mask"""
        dlg = wx.FileDialog(self,
                            "Which Mask File?",
                            wildcard="Numpy dump (npy)|*.npy|Text (dat)|*.dat",
                            style=wx.FD_OPEN)
        if dlg.ShowModal()==wx.ID_OK:
            path = dlg.GetPath()
            ext = path[-4:]
            if ext == ".dat":
                newmask = np.loadtxt(path,dtype=np.bool)
            else:
                newmask = np.load(path)
            self.mask = np.logical_and(self.mask,newmask)
            self.update()
        
        

    def OnSave(self,event):
        """Save the current 2D image to a file"""
        print("OnSave")
#        dlg=wx.FileDialog(self,"Choose graphics file",wildcard="Windows Bitmap (bmp)|*.BMP|Portable Network Graphic (png)|*.PNG|Joint Photographic Experts Group (jpg)|*.JPG|Portable Network Monocrome (pnm)|*.PNM|Tagged Image File Format (tif)|*.TIF|Archaic, useless format (pcx)|*.PCX",style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        dlg = self.imageSaveDialog
        if dlg.ShowModal()==wx.ID_OK:
            self.imPanel.saveImage(dlg.GetPath())

    def OnSpectrum(self,event):
        """Display a plot of the region of interest versus wavelength"""
        print("OnSpectrum")
        (xMin,xMax,yMin,yMax)=self.opPanel.getRoi()
        if type(self.data) is tuple:
            u3d,d3d = self.data
            u = np.sum(np.sum(u3d[yMin:yMax,xMin:xMax],0),0)
            d = np.sum(np.sum(d3d[yMin:yMax,xMin:xMax],0),0)
            uscale,dscale = self.scale
            self.specDlg.setScale(uscale,dscale)            
            self.specDlg.setData(u,d)
        else:
            u = np.sum(np.sum(self.data[yMin:yMax,xMin:xMax],0),0)
#            u *= self.scale
            self.specDlg.setScale(self.scale)
            self.specDlg.setData(u)
        self.specDlg.setIntensityRange(self.opPanel.getIntensityRange())
        self.specDlg.Show()

    def OnGrey(self,event):
        """Set the colormap to gray"""
        self.imPanel.cmap = cm.gray
        self.colorbar.setCmap(cm.gray)
        self.update()

    def OnHueVal(self,event):
        """Set the colormap to a rainbow"""
        self.imPanel.cmap = cm.jet
        self.colorbar.setCmap(cm.jet)
        self.update()

    def OnSpectral(self,event):
        """Set the colormap to the spectral map"""
        self.imPanel.cmap = cm.spectral
        self.colorbar.setCmap(cm.spectral)
        self.update()

    def OnPicker(self,event):
        """Let the user pick a color map from a list"""
        if self.cmp is None:
            self.cmp = ColorMapPicker(self,self.setColorMap)
        self.cmp.Show()

    def setColorMap(self,cmap):
        """Changes to the given colormap"""
        self.imPanel.cmap = cmap
        self.colorbar.setCmap(cmap)
        self.update()


    def OnExit(self,event):
        """Quit the program"""
        self.Close()

    def loadUpAndDown(self):
        """Read in spin flip data"""
        u3d,uscale = self.loadNormPel("Spin Up State")
        if u3d is None:
            return False
        del self.data
        d3d,dscale = self.loadNormPel("Spin Down State")
        self.data = (u3d,d3d)
        self.scale = (uscale,dscale)
        return True


    def OnPolar(self,event):
        """Display neutron polarization"""
        print("OnPolar")
        self.specDlg.setMode("polar")
        self.updateData = self.updateDataPolar
        self.update = self.updateSingle
        self.updateData()

    def OnFlipping(self,event):
        """Display the flipping ratio"""
        print("OnFlip")
        self.specDlg.setMode("flipping")
        self.updateData = self.updateDataFlip
        self.update = self.updateSingle
        self.updateData()

    def OnAnalysisSpinUp(self,event):
        """Display the Spin Up data"""
        print("OnSpinUp")
        self.specDlg.setMode("up")
        self.updateData = self.updateDataUp
        self.update = self.updateSingle
        self.updateData()

    def OnAnalysisSpinDown(self,event):
        """Display the Spin Down data"""
        print("OnSpinDown")
        self.specDlg.setMode("down")
        self.updateData = self.updateDataDown
        self.update = self.updateSingle
        self.updateData()

    def OnCopy(self,event):
        """Copy the image to a clipboard"""
        self.imPanel.copyToClipboard()
                


if __name__=="__main__":
    app=wx.PySimpleApp()
    pelvisframe = PelvisFrame(app.Yield)
    app.MainLoop()
