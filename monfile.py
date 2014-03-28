"""Classes for dealing with neutron monitor data

This module contains a single class: MonFile.  This class is used to read
the time, intensity, and spectrum information out of a file produced
by the SNS's BMM_server

"""

import numpy as np
import re
import scipy.interpolate as ip
import scipy.optimize as op
import matplotlib.pyplot as pyplot
from graphframe import GraphFrame
import pylab as pl
import math

class MonFile:
    """Manages a file which holds neutron monitor data."""
    KbT = 2.0e-3
    
    def __init__(self,file=None,plot=True):
        """Creates a MonFile object"""
        self.time = None #The amount of time that the monitor ran.
        self.spec = None #The neutron spectrum detected on the monitor.
        if file is not None:
            self.load(file,plot)

    def convertTime(self,t):
        """Converts a numpy array of time bins into neutron wavelengths"""
        distanceToG4 = 3.7338+2.5297
        #The distance between the end of G4 and the Helium 3 monitor.
        distanceToMonitor = 0.02 #FIXME
        t -= 860
        t *= 3.956034e-7/(distanceToMonitor+distanceToG4)/1e-10*1e-6
        return t

    def func(self, x, A, b, k, c):
        return A*x**2 * np.exp(-(x-k)**2*b) + c

    def load(self,file,plot=True):
        """Load data from the file given in the path string."""
        self.time = -1
        base = 0.1
        count = 0
        uplim = 31
        
        y = np.fromfile(file,np.int32,-1)
        x = np.arange(0,50001,1,dtype=np.float32)
        x = self.convertTime(x)
        #f = ip.interp1d(x,y)
        #p0 = [10., 0.0001, 10000., 2.]
        #p1, cov = op.curve_fit(self.func, x, y, p0)
        #print(p1)
        #p1f = self.func(x, *p1) #Fit of neutron monitor
        #xs = range(200)
        #xs = np.arange(0,35,0.1)
        #ys = np.zeros(350,dtype=np.uint32)

        xs = np.arange(0,uplim,base)
        ys = np.zeros(uplim/base,dtype=np.uint32)

        for (i,j) in zip(x,y):
            if i > base:
                ys[int(10*base-1)]=count
                base += 0.1
                count = 0
            count += j
        base = 0.1
        count = 0
        uplim = 31
            
        ymean = np.mean(ys[250:300])
        ynew = np.array([float(yo)-ymean*(uplim/base)/50001 for yo in y])
        
        ysnew = np.zeros(uplim/base,dtype=np.float32)
        for (i,j) in zip(x,ynew):
            if i > base:
                ysnew[int(10*base-1)]=count
                base += 0.1
                count = 0
            count += j

        if plot:
            graph = GraphFrame(None,"Monitor")
            graph2 = GraphFrame(None,"Monitor Adjusted")
        #        graph.plot(np.arange(0.0,20.0,0.1),f(xs))
        #    graph.plot(xs,ys)
            graph2.plot(xs,ysnew)          
        self.spec = np.expand_dims(np.expand_dims(y,axis=0),axis=0)

