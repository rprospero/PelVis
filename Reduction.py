from reader import PelFile
from monfile import MonFile
import matplotlib.pyplot as plt
import Combiner
import numpy as np
from optparse import OptionParser

basedir = "C:/userfiles/EXP011/"

def load(runs,current=None):
    paths = [basedir + "SESAME_%i/SESAME_%i_runinfo.xml"
             % (run,run) for run in runs]
    return Combiner.load(paths,current)


def export(runs,sortby,flipper,minmon=16,current=None):
    data = load(runs,current)

    keys = data.keys()

    if sortby is None:
        values = [""]
    else:
        values = set([x[sortby] for x in keys])

    base = basedir + "SESAME_%i/" % runs[-1]

    for value in values:
        ups = [x for x in keys if x[flipper] > 0 
               and (sortby is None or x[sortby] == value)]
        downs = [x for x in keys if x[flipper] < 0 
                  and (sortby is None or x[sortby] == value)]
#        if current is not None:
#            value += "_%i_"%current
        if type(value) is not str:
            value = ("%0.3f"%float(value))
        if ups != []:
            Combiner.save(base+value+"up",
                          minmon,
                          ups,
                          data)
        if downs != []:
            Combiner.save(base+value+"down",
                          minmon,
                          downs,
                          data)
def spectrum(run,name,mins=(0,0),maxs=(16,128)):
    name = "%0.3f"%float(name)
    p = PelFile(basedir+"SESAME_%i/" % run + name+"up_neutron_event.dat")
    mon = MonFile(basedir+"SESAME_%i/" % run + name+"up_bmon_histo.dat",False)
    up = p.make1d(mins,maxs)/np.sum(mon.spec)
    p = PelFile(basedir+"SESAME_%i/" % run + name+"down_neutron_event.dat")
    mon = MonFile(basedir+"SESAME_%i/" % run + name+"down_bmon_histo.dat",False)
    down = p.make1d(mins,maxs)/np.sum(mon.spec)

    return (up-down)/(up+down)

def fr(run,name,mins=(183,227),maxs=(234,302)):
    p = PelFile(basedir+"%04i/" % run + name+"up.pel")
    mon = MonFile(basedir+"%04i/" % run + name+"up.pel.txt",False)
    up = p.make1d(mins,maxs)/np.sum(mon.spec)
    p = PelFile(basedir+"%04i/" % run + name+"down.pel")
    mon = MonFile(basedir+"%04i/" % run + name+"down.pel.txt",False)
    down = p.make1d(mins,maxs)/np.sum(mon.spec)

    return np.sum(up[50:100])/np.sum(down[50:100])

def singleplot(run,name,mins=(148,223),maxs=(240,302)):
    data = spectrum(run,name,mins,maxs)
    data[np.isnan(data)]=0
    plt.plot(np.arange(200)*0.1,data,"r-")
    plt.show()

def echoplot(run,names,mins=(0,0),maxs=(16,128),outfile=None):

    data = np.vstack(tuple([spectrum(run,name,mins,maxs) for name in names]))
    data[np.isnan(data)]=0
    data = data[:,0:100]
    xs = np.arange(101)*0.1
    ys = sorted([float(x) for x in names])
    ys += [ys[-1]+ys[1]-ys[0]] #Add last element
    ys = np.array(ys)
    print ys
    plt.pcolor(xs,ys,data,vmin=-1,vmax=1)
    if outfile is None:
        plt.show()
    else:
        print name
        plt.savefig(outfile)
        plt.clf()

def echofr(run,names,mins=(148,223),maxs=(240,302),outfile=None):
    data = np.array([fr(run,name,mins,maxs) for name in names])
    data[np.isnan(data)]=0
    xs = np.array([float(x) for x in names])
    plt.plot(xs,data)
    if outfile is None:
        plt.show()
    else:
        plt.savefig(outfile)
        plt.clf()

def echodiff(run,names,split,mins,maxs,outfile=None):
    data = np.vstack(tuple([np.arccos(spectrum(run,name,mins,(split,302))) - 
                            np.arccos(spectrum(run,name,(split,223),maxs)) for name in names]))

    data[np.isnan(data)]=0
    data = data[:,0:100]

    xs = np.arange(100)*0.1
    ys = np.array([float(x) for x in names])
    plt.pcolor(xs,ys,data,vmin=-np.pi,vmax=np.pi)
    if outfile is None:
        plt.show()
    else:
        print name
        plt.savefig(outfile)
        plt.clf()

if __name__=='__main__':

    parser = OptionParser()

    choices = {None:None,"flipper":0,"guides":1,"phase":2,"sample":3,"1":4,"2":5,"3":6,"4":7,"5":8,"6":9,"7":10,"8":11}

    parser.add_option("-e","--export",action="store_true",help="Export into pel files")
    parser.add_option("--sortby",action="store",type="choice",help="Which power supply is scanned",
                      choices=choices.keys())
    parser.add_option("--flip",action="store",type="choice",help="Which power supply runs the flipper",
                      choices=choices.keys(),default="guides")
    parser.add_option("--mon",action="store",type="float",help="Minimum monitor value.  If the value is lessthan or equal to zero, all runs are included, regardless of monitor count.",default=8)

    parser.add_option("--xmin",action="store",type="int",help="Minimum x value",default=0)
    parser.add_option("--ymin",action="store",type="int",help="Minimum y value",default=0)
    parser.add_option("--xmax",action="store",type="int",help="Maximum x value",default=16)
    parser.add_option("--ymax",action="store",type="int",help="Maximum y value",default=128)

    parser.add_option("--start",action = "store",type="float", help="The starting current of the scan")
    parser.add_option("--stop",action = "store", type="float", help="The ending current of the scan")
    parser.add_option("--step",action = "store", type="float", help="The current step of the scan")

    parser.add_option("--plot",action="store",type="choice",
                      help="Where to make a simple plot or perform a height diff",
                      choices=["plot","diff","fr","echo"])

    parser.add_option("--current",action="store",type="int",
                      default=None,
                      help="A triangle current to filter the results.")

    (options,runs) = parser.parse_args()

    runs = [int(x) for x in runs]

    if options.export:
        export(runs,choices[options.sortby],choices[options.flip],options.mon,options.current)

    if options.plot is None:
        pass
    else:
        if options.sortby is None:
            names = [""]
        else:
            count = round((options.stop-options.start)/options.step)+1
            names = [str(x) 
                     for x in 
                     np.linspace(
                    options.start,
                    options.stop,
                    count)]
        if options.plot=="plot":
            print runs
            print names
            singleplot(runs[-1],names[0],(options.xmin,options.ymin),(options.xmax,options.ymax))
        elif options.plot=="fr":
            echofr(runs[-1],names,(options.xmin,options.ymin),(options.xmax,options.ymax))
        elif options.plot=="diff":
            echodiff(runs[-1],names,187(options.xmin,options.ymin),(options.xmax,options.ymax))
        elif options.plot=="echo":
            echoplot(runs[-1],names,(options.xmin,options.ymin),(options.xmax,options.ymax))

