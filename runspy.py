from optparse import OptionParser
import xml.etree.ElementTree as ET
import HTMLParser
import json
import os.path
import matplotlib.pyplot as plt
import numpy as np


basedir = "C:/userfiles/EXP011/"
XMLNS = "{http://neutrons.ornl.gov/SNS/DAS/runinfo_v4_3}"

def plot(d):
    form = {-5:"r*",5:"kh"}
    labels = {-5:"Spin Up",5:"Spin Down"}
    plt.xlabel("Run Number",fontsize=30)
    plt.ylabel("Normalized Count Rate",fontsize=30)
    plt.xticks(fontsize="20")
    plt.yticks(fontsize="20")
    for k in d.keys(): 
        paths = [os.path.join(basedir,"SESAME_%i"%run,
                     "SESAME_%i_neutron_event.dat"%run)
                 for run in d[k]]
        mons = [os.path.join(basedir,"SESAME_%i"%run,
                     "SESAME_%i_bmon_histo.dat"%run)
                 for run in d[k]]
        points = np.asarray(
            [len(np.fromfile(path,count=-1,dtype=np.int32)[::2])
             for path in paths],dtype=np.float64)
        norms = np.asarray(
            [np.sum(np.fromfile(path,count=-1,dtype=np.int32))
             for path in mons])
        plt.errorbar(d[k],points/norms,yerr=np.sqrt(points)/norms,fmt=form[k],markersize=10)
    plt.legend(labels.values(),numpoints=1)
    plt.show()
       

def process(runs):
    d = {}
    for run in runs:
        path = os.path.join(basedir,"SESAME_%i"%run,
                            "SESAME_%i_runinfo.xml"%run)
        text = ET.parse(path).getroot().find(".//"+XMLNS+"Notes").text 
        text = HTMLParser.HTMLParser().unescape(text)
        try:
            manifest = json.loads(text)
        except:
            print("No current information stored for run %i"%run)
            continue #Yes, I know this is an anti-pattern,
        
        flip = manifest['Flipper']
        old = d.get(flip,[])[:]
        old.append(run)
        d[flip]=old
    return d

if __name__=='__main__':

    parser = OptionParser()

    (options,runs) = parser.parse_args()

    runs = range(int(runs[0]),int(runs[1]))

    data = process(runs)
    plot(data)
