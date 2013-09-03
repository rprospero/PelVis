import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
import sys
from time import strptime,mktime

XMLNS = "{http://neutrons.ornl.gov/SNS/DAS/runinfo_v4_3}"

BASEPATH = "C:/userfiles/EXP011/SESAME_%i/"

def getRate(run):
    format = "%Y-%m-%dT%H:%M:%S-04:00"
    monpath = BASEPATH%run + "SESAME_%i_bmon_histo.dat"%run
    count = np.sum(np.fromfile(monpath,dtype=np.int32))

    root = ET.parse(BASEPATH%run + "SESAME_%i_runinfo.xml"%run).getroot()
    starttime = strptime(root.find(".//"+XMLNS+"StartTime").text.strip(),format)
    stoptime = strptime(root.find(".//"+XMLNS+"StopTime").text.strip(),format)
    diff = mktime(stoptime) - mktime(starttime)

    return [count/diff,np.sqrt(count)/diff]

start = int(sys.argv[1])
stop = int(sys.argv[2])

runs = np.arange(start,stop)
rates = np.array([getRate(x) for x in runs])

plt.errorbar(runs,rates[:,0],yerr=rates[:,1])
plt.show()
