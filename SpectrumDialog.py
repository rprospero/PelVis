"""Classes for dealing with neutron spectra

This module contains a single class:  SpectrumDialog.  This dialog
handles all of the options and parameters for creating spectrum
plots of intensities and polarization.  This class also handles
automated rebinning of data.

"""

import wx
import numpy as np
from graphframe import GraphFrame

RESOLUTION = 400

class SpectrumDialog(wx.Dialog):
    """A dialog to set the options on a spectrum plot"""

    def __init__(self,parent=None):
        """Create a SpectrumDialog"""
        wx.Dialog.__init__(self,parent,wx.ID_ANY,"Spectrum Options")
        sizer = wx.GridBagSizer()

#        self.datacount = 0
        self.up = None #The spin up data array
        self.down = None #The spin down data array

        #A dictionary of the available manipulations to perform
        #on the data before plotting it.
        self.modes = {"up":self.spinUp,
                      "down":self.spinDown,
                      "polar":self.polar,
                      "flipping":self.flipping}
        self.calcSpec = self.spinUp #The current data manipulation function
        
        saveButton = wx.Button(self,-1,"Save Spectrum")
        viewButton = wx.Button(self,-1,"View Spectrum")
        viewButton.Bind(wx.EVT_BUTTON,self.onView)
        saveButton.Bind(wx.EVT_BUTTON,self.onSave)
        
        sizer.Add(wx.StaticText(self,-1,"Minimum Percent Error"),
                  pos=wx.GBPosition(0,0), flag=wx.EXPAND)
        #An input box for the user's chosen percentage error
        self.minerr = wx.TextCtrl(self,-1,"10")
        sizer.Add(self.minerr,pos=wx.GBPosition(0,1), flag=wx.EXPAND)

        #A checkbox for whether the user wants the data autobinned
#        self.binbox = wx.CheckBox(self,-1,"Auto binning")
        self.nobinrad = wx.RadioButton(self,-1,"Raw Data",style=wx.RB_GROUP)
        self.autobinrad = wx.RadioButton(self,-1,"Auto binning")
        self.setbinrad = wx.RadioButton(self,-1,"Fixed Binning")
#        sizer.Add(self.binbox,pos=wx.GBPosition(1,0),flag=wx.EXPAND,
#                  span=wx.GBSpan(1,2))
        sizer.Add(self.nobinrad,wx.GBPosition(1,0),flag=wx.EXPAND)
        sizer.Add(self.autobinrad,wx.GBPosition(1,1),flag=wx.EXPAND)
        sizer.Add(self.setbinrad,wx.GBPosition(1,2),flag=wx.EXPAND)
        
        sizer.Add(saveButton,pos=wx.GBPosition(2,0),flag=wx.EXPAND)
        sizer.Add(viewButton,pos=wx.GBPosition(2,1),flag=wx.EXPAND)
        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
#        self.bin=True

    def setData(self,up,down=None):
        """Sets the spin up and spin down spectra.  Expects two numpys arrays"""
        del self.up
        del self.down
        up[up < 0.0] = 0.0
        if down is not None:
            down[down < 0.0] = 0.0
        self.up=up
        self.down=down

    def setScale(self,up,down=None):
        """Sets the scaling constants for the spin up and spin down states.

        To calculate error, we need the raw neutron counts, not just the
        monitor normalized ones.  This function accepts the monitor counts
        used to do the initial scaling on the detector data, so that
        the raw counts can be recalculated.

        """
        self.uscale=up
        self.dscale=down

    def setIntensityRange(self,range):
        """Set the minimum and maximum y axis for plotting"""
        self.vmin,self.vmax = range

    def onView(self,event):
        """Display a graph of the spectrum."""
        x,y,e = self.calcSpec()
        graph = GraphFrame(self,"Spectrum")
        graph.plot(x,y,range=(self.vmin,self.vmax),yerr=e)
        self.Show(False)

    def onSave(self,event):
        """Save a graph of the spectrum to a file."""
        x,y,e = self.calcSpec()
        dialog=wx.FileDialog(self,"Name the spectm file",
                             wildcard="ASCII (dat)|*.dat",
                             style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal()==wx.ID_OK:
            with open(dialog.GetPath(),"w") as stream:
                for i in range(len(x)):
                    stream.write("%f\t%f\t%f\n"%(x[i],y[i],e[i]))
        self.Show(False)

    def setMode(self,mode):
        """Chooses the calculation to perform on the data

        Keyword arguments:
        mode -- a string describing which function out of self.modes
                should be performed on the data.

        """
        self.calcSpec = self.modes[mode]

    def autobinset(self):
        """Rebins both up and down data based on the user's chosen error."""
        x=[]
        u=[]
        d=[]
        count=0 #number of channels combined since last binning
        utot=0 #counts in the up state
        dtot=0 #counts in the down state
        #If there's no chosen error bounds, just return the original data.
        if self.nobinrad.GetValue():
            return (np.arange(0.0,RESOLUTION)*20.0/RESOLUTION
                    ,self.up,self.down)
        #If we're going any sort of binning, we'll need raw values
        up=self.up*self.uscale
        down=self.down*self.dscale
        #Check for autobinning
        if self.autobinrad.GetValue():
            #The maximum percentage error in the spin up or spin down state
            emax = float(self.minerr.GetValue())/100.0
            for i in range(len(self.up)):
                utot += up[i]
                dtot += down[i]
                uerr = 1.0/np.sqrt(utot)#error in the up state
                derr = 1.0/np.sqrt(dtot)#error in the down state
                #if the error is below the threshold, add the new data point
                if uerr <= emax and derr <= emax:
                    u.append(utot/self.uscale)
                    d.append(dtot/self.dscale)
                #choose x as the center of the binned data
                    x.append((i-0.5*count)*0.1)
                    i = 0
                    utot=0
                    dtot=0
                    count=0
                else:
                    count += 1
            return (np.array(x),
                    np.array(u),
                    np.array(d))
        elif self.setbinrad.GetValue():
            count = int(self.minerr.GetValue())
            x = [np.mean(y) for y in 
                 np.array_split(np.arange(0.0,RESOLUTION)*20.0/RESOLUTION,count)]
            u = [np.sum(y)/self.uscale for y in np.array_split(up,count)]
            d = [np.sum(y)/self.dscale for y in np.array_split(down,count)]
            print((x,u,d))
            return (np.array(x),
                    np.array(u),
                    np.array(d))
        else:
            raise RuntimeException("Need to Implement bullet choice!")

    def autobin(self,up,scale):
        """Rebins one data array based on the user's chosen error

        Keyword arguments:
        up -- the array to be rebinned
        scale -- the conversion factor used to normalize against monitor

        """
        if self.nobinrad.GetValue():
            return (np.arange(0.0,RESOLUTION)*20.0/RESOLUTION,up/scale)
        elif self.autobinrad.GetValue():
            x=[]
            u=[]
            count=0
            utot=0
            #The maximum percentage error in the spin up or spin down state
            emax = float(self.minerr.GetValue())/100.0
            for i in range(len(self.up)):
                utot += up[i]
                uerr = 1.0/np.sqrt(utot)
                if uerr < emax:
                    u.append(utot/scale/(count+1))
                    x.append((i-0.5*count)*0.1)
                    count = 0
                    utot=0
                else:
                    count += 1
            return (np.array(x),np.array(u))
        elif self.setbinrad.GetValue():
            count = int(self.minerr.GetValue())
            x = np.arange(0.0,RESOLUTION)*20.0/RESOLUTION
            x = np.array([np.mean(y) for y in np.array_split(x,count)])
            u = np.array([np.sum(y)/scale for y in np.array_split(up,count)])
            return (x,u)

    def flipping(self):
        """Calculate the flipping ratio"""
        if self.down is not None:
            (x,u,d)=self.autobinset()
            y = u/(d+1e-6)
            uerr = np.sqrt(u*self.uscale)/self.uscale
            derr = np.sqrt(d*self.dscale)/self.dscale
            e = y*np.sqrt((uerr/u)**2+(derr/d)**2)
            return (x,y,e)

    def polar(self):
        """Calculate the polarization"""
        if self.down is not None:
            (x,u,d)=self.autobinset()
            print((x,u,d))
            y = (u-d)/(u+d+1e-6)
            u *= self.uscale
            d *= self.dscale
            e = y*(np.sqrt(u+d))
            e *= (1.0/(u-d)+1.0/(u+d))
            return (x,y,e)

    def spinUp(self):
        """Calculate the spin up intensity"""
        (x,y)=self.autobin(self.up*self.uscale,self.uscale)
        return (x,y,np.sqrt(y*self.uscale)/self.uscale)

    def spinDown(self):
        """Calculate the spin down intensity"""
        if self.down is not None:
            (x,y)=self.autobin(self.down*self.dscale,self.dscale)
            return (x,y,np.sqrt(y*self.dscale)/self.dscale)

