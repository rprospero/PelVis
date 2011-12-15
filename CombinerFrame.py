"""This module contains an application for combining runs files"""

from XMLManifest import XMLManifest
#from XMLConfig import XMLConfig
import wx
import numpy as np
import os.path

class CombinerFrame(wx.Frame):
    """This window is the main interaction point for combining runs"""
    def __init__(self,parent=None):
        """This method creates a CombinerFrame"""
        wx.Frame.__init__(self,parent,wx.ID_ANY,"Combine Data Runs")
        sizer = wx.GridBagSizer()

        #Create window contents
        self.listbox = wx.ListBox(self,-1,style=wx.LB_MULTIPLE,
                                  size=wx.Size(500,150))
        addbutton = wx.Button(self,wx.ID_ADD)
        removebutton = wx.Button(self,wx.ID_REMOVE)
        self.monctrl = wx.TextCtrl(self,-1,"8.0")
        combinebutton = wx.Button(self,wx.ID_SAVE)

        #Connect buttons to event handlers
        addbutton.Bind(wx.EVT_BUTTON,self.onAdd)
        removebutton.Bind(wx.EVT_BUTTON,self.onRemove)
        combinebutton.Bind(wx.EVT_BUTTON,self.onSave)


        #Add components to window
        sizer.Add(self.listbox,pos=wx.GBPosition(0,0),
                  flag=wx.EXPAND,span=wx.GBSpan(1,8))
        sizer.Add(addbutton,pos=wx.GBPosition(1,0),
                  flag=wx.EXPAND,span=wx.GBSpan(1,2))
        sizer.Add(removebutton,pos=wx.GBPosition(1,2),
                  flag=wx.EXPAND,span=wx.GBSpan(1,2))
        sizer.Add(wx.StaticText(self,-1,"Monitor Minimum: "),
                                    pos=wx.GBPosition(1,4),
                                    span=wx.GBSpan(1,2))
        sizer.Add(self.monctrl,pos=wx.GBPosition(1,6),flag=wx.EXPAND,
                  span=wx.GBSpan(1,2))
        sizer.Add(combinebutton,pos=wx.GBPosition(2,0),
                  flag=wx.EXPAND,span=wx.GBSpan(1,8))        

        sizer.SetSizeHints(self)
        self.SetSizer(sizer)
        self.Show()

    def onAdd(self,event):
        """Add another manifest to be combined"""
        dlg=wx.FileDialog(self,"Choose the Manifest",
                          wildcard="SESAME manifest|Manifest.xml|Generic Manifest|*.xml",style=wx.FD_OPEN|wx.FD_MULTIPLE)
        if dlg.ShowModal()==wx.ID_OK:
            paths = dlg.GetPaths()
            for path in paths:
                self.listbox.Insert(path,0)

    def onRemove(self,event):
        """Drop a manifest from the list"""
        indices = self.listbox.GetSelections()
        count=0 #How many files we've dropped thus far
        for i in indices:
            self.listbox.Delete(i-count)
            count+=1

    def onSave(self,event):
        """Combine the manifests"""
        paths = self.listbox.GetItems()
        dlg = wx.FileDialog(self,"Save PEL file",wildcard="PEL file|*.pel",
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal()!=wx.ID_OK:
            return
        outfile = dlg.GetPath()[:-4]
        final = {}#Dictionary of flipper currents

        minmon = float(self.monctrl.GetValue())#Monitor cutoff for live beam

        #Get the subruns organized by flipper current
        for path in paths:
            base = os.path.dirname(path)
            manifest = XMLManifest(path,0)
            runDict = manifest.getRuns(base)
            for key in runDict:
                runs = runDict[key]
                if key in final:
                    final[key].extend(runDict[key])
                else:
                    final[key] = runDict[key]

        #Combine each flipper current
        print(final)
        for key in final:
            runs = final[key]
            mon = np.zeros((1001,),dtype=np.int32)
            tottime = 0
            totmon = 0
            totdet = 0
            with open(outfile+"_"+str(key)+".pel","wb") as pelfile:
                _,_,_,_,_,detpath=runs[0]
                with open(detpath,"rb") as infile:
                    header = np.fromfile(infile,dtype=np.int8,count=256)
                    header.tofile(pelfile)
                    del header
                #load the individual subruns
                for r in runs:
                    num,time,moncount,monpath,detcount,detpath=r
                    if float(moncount)/float(time) < minmon:
                        print("Dropping subrun %s as the count rate is too low"%num)
                        continue
                    tottime += float(time)
                    totmon += int(moncount)
                    totdet += int(detcount)
                    with open(monpath,"r") as infile:
                        print(monpath)
                        montemp = np.loadtxt(infile,dtype=np.int32,skiprows=3)
                        mon += montemp[:,1]
                    with open(detpath,"rb") as infile:
                        infile.seek(256)
                        dettemp = np.fromfile(infile,count=-1)
                        dettemp.tofile(pelfile)
                        del dettemp
            with open(outfile+"_"+str(key)+".txt","w") as stream:
                stream.write("File Saved for Run Number %s.\n"%0)
                stream.write("This run had %d counts " % np.sum(mon))
                stream.write("and lasted %d milliseconds\n" % (float(tottime)*1000))
                stream.write("User Name=Unkown, Proposal Number=Unknown\n")
                for i in range(0,1000):
                    stream.write("%d\t%d\n"%(i+1,mon[i]))

if __name__=="__main__":
    app = wx.PySimpleApp()
    f = CombinerFrame()
    app.MainLoop()
