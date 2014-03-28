import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
import time
from reader import PelFile
from monfile import MonFile
import sys
import os.path
import xml.etree.ElementTree as ET
import HTMLParser
import json

RUN = 32725
basedir = "C:/userfiles/EXP011/"
XMLNS = "{http://neutrons.ornl.gov/SNS/DAS/runinfo_v4_3}"
REBIN = 4

plt.ion()

def spectrum(run,mins=(0,0),maxs=(16,128),mask=None):
    eventfile = basedir+"SESAME_%i/SESAME_%i" % (run,run) + "_neutron_event.dat"
    if not os.path.isfile(eventfile):
        return None
    p = PelFile(eventfile)
    mon = MonFile(basedir+"SESAME_%i/SESAME_%i" % (run,run) +"_bmon_histo.dat",False)
    up = p.make1d(mins,maxs,mask)

    manifestFile = basedir+"SESAME_%i/SESAME_%i" % (run,run) + "_runinfo.xml"

    text = ET.parse(manifestFile).getroot().find(".//"+XMLNS+"Notes").text
    text = HTMLParser.HTMLParser().unescape(text)
    manifest = json.loads(text)

    return up,np.sum(mon.spec),manifest

mpl.rcParams['interactive'] = True

def manifestly(start):
    i = start
    while True:
        manifestFile = basedir+"SESAME_%i/SESAME_%i" % (i,i) + "_runinfo.xml"
        monitorFile = basedir+"SESAME_%i/SESAME_%i" % (i,i) + "_bmon_histo.dat"
        if not os.path.isfile(monitorFile):
            #If the monitor file hasn't been written, the run isn't
            #done yet and we shouldnt' read it
            yield None
        else:
            try:
                manifestFile = basedir+"SESAME_%i/SESAME_%i" % (i,i) + "_runinfo.xml"

                text = ET.parse(manifestFile).getroot().find(".//"+XMLNS+"Notes").text
                text = HTMLParser.HTMLParser().unescape(text)
                manifest = json.loads(text)
                yield i,manifest
                i += 1
            except ValueError:
                yield None


def spectra(gen):
    while True:
        next = gen.next()
        if next is None:
            yield None
            continue
        i,_=next
        s = spectrum(i)
        if s is None:
            yield None
        else:
            data,counts,manifest = s
            yield data,counts,manifest
            print i
            print(manifest)
            i += 1

def filter(gen,f):
    next = gen.next()
    while True:
        if next is None:
            yield None
        else:
            if f(next):
                yield next
        next = gen.next()

def integrator(gen):
    data = np.zeros(400/REBIN)
    counts = 0
    while True:
        next = gen.next()
        if next is not None:
            data += rebin(next[0],REBIN)
            counts += next[1]
        yield data/counts,np.sqrt(data)/counts
        

def joiner(gens):
    while True:
        streams = [g.next() for g in gens]
        yield streams

def plotter(source,count=1):
    xs = np.arange(0,20,0.05*REBIN) 
    plt.figure("Live Update")
    plt.ylim([-1,1])
    graphs = [plt.errorbar(xs,np.zeros(400/REBIN),np.zeros(400/REBIN),marker="o") for i in range(count)]
    while True:
        data=source.next()
        for g,d in zip(graphs,data):
            if d is not None:
                g[0].set_ydata(d)
        plt.draw()
        plt.pause(5)

def polarization(up,down):
    up = integrator(up)
    down = integrator(down)
    while True:
        u = up.next()[0]
        d = down.next()[0]
        yield -1*(u-d)/(u+d)
        #yield d/u

def fullpol(i,f):
    upstate = lambda x: x[1]['Flipper'] < 0
    downstate = lambda x: x[1]['Flipper'] > 0

    ups = spectra(filter(filter(manifestly(i),upstate),f))
    downs = spectra(filter(filter(manifestly(i),downstate),f))
    return polarization(ups,downs)

def rebin(x,bins):
    result=np.zeros(len(x)/bins,dtype=np.float64)
    for b in range(bins):
        result += x[b::bins]
    return result

if __name__=="__main__":

    lowcur = lambda x: x[1]['Triangle1'] ==3
    midcur = lambda x: x[1]['Triangle1'] ==9
    hicur = lambda x: x[1]['Triangle1'] ==15

    start = int(sys.argv[1])

    filters = [lambda x: x[1]['Triangle1'] == float(i) for i in sys.argv[2:]]

    polarizers = [fullpol(start,f) for f in filters]

    p = plotter(joiner(polarizers),count=len(polarizers))
    plotter(p)
