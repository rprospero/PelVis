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

def getIntegratedSpectra(run,name,mins,maxs):
    name = "%0.3f"%float(name)
    p = PelFile(basedir+"SESAME_%i/" % run + name+"up_neutron_event.dat")
    mon = MonFile(basedir+"SESAME_%i/" % run + name+"up_bmon_histo.dat",False)
    up = np.sum(p.make1d(mins,maxs,mask)[30:100])
    uperr = np.sqrt(up)/np.sum(mon.spec)
    up /= np.sum(mon.spec)
    p = PelFile(basedir+"SESAME_%i/" % run + name+"down_neutron_event.dat")
    mon = MonFile(basedir+"SESAME_%i/" % run + name+"down_bmon_histo.dat",False)
    down = np.sum(p.make1d(mins,maxs,mask)[30:100])
    downerr = np.sqrt(down)/np.sum(mon.spec)
    down /= np.sum(mon.spec)

    return (up,uperr,down,downerr)


def spectrum(run,name,mins=(0,0),maxs=(16,128),mask=None):
    if name != '':
        name = "%0.3f"%float(name)
    p = PelFile(basedir+"SESAME_%i/" % run + name+"up_neutron_event.dat")
    mon = MonFile(basedir+"SESAME_%i/" % run + name+"up_bmon_histo.dat",False)
    up = p.make1d(mins,maxs,mask)
    uperr = np.sqrt(up)/np.sum(mon.spec)
    up /= np.sum(mon.spec)
    p = PelFile(basedir+"SESAME_%i/" % run + name+"down_neutron_event.dat")
    mon = MonFile(basedir+"SESAME_%i/" % run + name+"down_bmon_histo.dat",False)
    down = p.make1d(mins,maxs,mask)
    downerr = np.sqrt(down)/np.sum(mon.spec)
    down /= np.sum(mon.spec)

    return (up-down)/(up+down)

def simple_spectrum(run,mins=(0,0),maxs=(16,128),mask=None):
    p = PelFile(basedir+"SESAME_%i/SESAME_%i_neutron_event.dat"%(run,run))    
    mon = MonFile(basedir+"SESAME_%i/SESAME_%i_bmon_histo.dat"%(run,run),False)    
    data = p.make1d(mins,maxs,mask)
    err = np.sqrt(data)/np.sum(mon.spec)
    data /= np.sum(mon.spec)

    return (data,err)

def fr(run,name,mins=(0,0),maxs=(16,128),mask=None):
    up,uperr,down,downerr = getIntegratedSpectra(run,name,mins,maxs,mask)

    ratio = down/up
    rerr = ratio * np.sqrt((uperr/up)**2+(downerr/down)**2)

    return (ratio,rerr)

def run_int(run,name,mins=(0,0),maxs=(16,128),mask=None):
    up,uperr,down,downerr = getIntegratedSpectra(run,name,mins,maxs,mask)

    total = up+down
    total_err = np.sqrt(uperr**2+downerr**2)

    return (total,total_err)


def singleplot(run,name,mins=(0,0),maxs=(16,128)):
    data = spectrum(run,name,mins,maxs)
    data[np.isnan(data)]=0
    plt.plot(np.arange(200)*0.1,data,"r-")
    plt.show()

def echoplot(run,names,mins=(0,0),maxs=(16,128),mask=None,outfile=None):

    data = np.vstack(tuple([spectrum(run,name,mins,maxs,mask) for name in names]))
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

def intensity(run,names,mins=(0,0),maxs=(16,128),mask=None,outfile=None):
    names = [name for name in names if float(name) != 5.475]
    data = [run_int(run,name,mins,maxs,mask) for name in names]
    errs = np.array([x[1] for x in data])
    data = np.array([x[0] for x in data])
    data[np.isnan(data)]=0
    errs[np.isnan(data)]=1
    xs = np.array([float(x) for x in names])
    plt.errorbar(xs,data,yerr=errs)
#    if outfile is None:
    plt.show()
    if outfile is not None:
        np.savetxt(outfile,np.transpose(np.vstack((xs,data,errs))))

    

def echofr(run,names,mins=(0,0),maxs=(16,128),mask=None,outfile=None):
    names = [name for name in names if float(name) != 5.475]
    print names
    data = [fr(run,name,mins,maxs,mask) for name in names]
    errs = np.array([x[1] for x in data])
    data = np.array([x[0] for x in data])
    data[np.isnan(data)]=0
    errs[np.isnan(data)]=1
    xs = np.array([float(x) for x in names])
    plt.errorbar(xs,data,yerr=errs)
#    if outfile is None:
    plt.show()
    if outfile is not None:
        np.savetxt(outfile,np.transpose(np.vstack((xs,data,errs))))
    #trying the fitting
    data = (data-1.0)/(data+1.0)
    print(data)
    data = np.log(data)
    fit = np.polyfit(xs,data,2)
    a = fit[0]
    b = fit[1]
    c = fit[2]
    print(fit)
    plt.plot(xs,np.exp(data),"b*")
    plt.plot(xs,np.exp(c+b*xs+a*xs**2),"r-")
    plt.show()
    print(-1*b/(2*a))

def poldrift(runs,mins,maxs,outfile=None):
    if len(runs)%2 == 1:
        runs = runs[:-1]
    ups = [simple_spectrum(run,mins,maxs)
                           for run in runs[1::2]]
    downs = [simple_spectrum(run,mins,maxs)
                           for run in runs[0::2]]
    uperrs = np.array([np.sqrt(np.sum(run[1]**2)) for run in ups])
    downerrs = np.array([np.sqrt(np.sum(run[1]**2)) for run in downs])
    ups = np.array([np.sum(run[0]) for run in ups])
    downs = np.array([np.sum(run[0]) for run in downs])
    p = ups/downs
    err = p * np.sqrt((uperrs/ups)**2+(downerrs/downs)**2)
    xs = np.array(runs[0::2])
    plt.errorbar(xs,p,yerr=err)
    plt.show()
    if outfile is not None:
        np.savetxt(outfile,np.transpose(np.vstack((xs,p,err))))

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
    parser.add_option("--skip",action = "append", type="int", help="Marks that a run should NOT be included in the file export.")

    parser.add_option("--plot",action="store",type="choice",
                      help="Where to make a simple plot or perform a height diff",
                      choices=["plot","diff","fr","echo","intensity","poldrift"])
    parser.add_option("--save",action="store",type="string",default=None,
                      help="A file in which to save the dataset.")
    parser.add_option("--mask",action="store",type="string",default=None,
                      help="A mask file indicating which pixel to use in the analysis")
    parser.add_option("--current",action="store",type="int",
                      default=None,
                      help="A triangle current to filter the results.")

    (options,runs) = parser.parse_args()

    runs = range(int(runs[0]),int(runs[1]))
    runs = [r for r in runs if r != 648] #remove run where He3 was flipped
    for item in options.skip:
        runs.remove(item)

    if options.export:
        export(runs,choices[options.sortby],choices[options.flip],options.mon,options.current)

    if options.mask is not None:
        if options.mask[-3:] == "dat":
            mask = np.loadtxt(options.mask)
        else:
            mask = np.load(options.mask)
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
            echofr(runs[-1],names,(options.xmin,options.ymin),(options.xmax,options.ymax),outfile=options.save)
        elif options.plot=="diff":
            echodiff(runs[-1],names,187(options.xmin,options.ymin),(options.xmax,options.ymax),options.save)
        elif options.plot=="echo":
            echoplot(runs[-1],names,(options.xmin,options.ymin),(options.xmax,options.ymax),outfile=options.save)
        elif options.plot=="intensity":
            intensity(runs[-1],names,(options.xmin,options.ymin),(options.xmax,options.ymax),outfile=options.save)
        elif options.plot=="poldrift":
            poldrift(runs,(options.xmin,options.ymin),(options.xmax,options.ymax),outfile=options.save)

