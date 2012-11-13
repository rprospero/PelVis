import xml.etree.ElementTree as ET
import HTMLParser
import json
import numpy as np
import os.path
from time import strptime,mktime
from math import floor

XMLNS = "{http://neutrons.ornl.gov/SNS/DAS/runinfo_v4_3}"

def load(paths,filter=None):
    currents = set([])#List of the configurations of the instrument
    runsets = {}#Directionary of lists of run nodes, indexed by their instrument configuration

    for path in paths:
        base = os.path.dirname(path)
        text = ET.parse(path).getroot().find(".//"+XMLNS+"Notes").text 
        text = HTMLParser.HTMLParser().unescape(text)
        try:
            manifest = json.loads(text)
        except:
            print("Failed: %s"%path)
            continue
        
        if ((filter is not None) and 
            (floor(float(manifest['triangle1'])) != filter)):
            continue #wrong triangle current
        current = (manifest['Flipper'],
                   manifest['Guide'],
                   manifest['Phase'],
                   manifest['Sample'],
                   manifest['Triangle1'],
                   manifest['Triangle2'],
                   manifest['Triangle3'],
                   manifest['Triangle4'],
                   manifest['Triangle5'],
                   manifest['Triangle6'],
                   manifest['Triangle7'],
                   manifest['Triangle8'])
        if current in currents:
            runsets[current].append(path)
        else:
            currents.add(current)
            runsets[current]=[path]
    return runsets

def save(path,minmon,keys,runsets):
    runs = [x for key in keys for x in runsets[key]]
    mon = np.zeros((50001,),dtype=np.int32)
    format = "%Y-%m-%dT%H:%M:%S-04:00"
    with open(path+"_neutron_event.dat","wb") as outfile:
        for r in runs:
            monpath = r[:-11] + "bmon_histo.dat"
            detpath = r[:-11] + "neutron_event.dat"
            starttime = strptime(ET.parse(r).getroot().find(".//"+XMLNS+"StartTime").text.strip(),format)
            stoptime = strptime(ET.parse(r).getroot().find(".//"+XMLNS+"StopTime").text.strip(),format)

            time = mktime(stoptime)-mktime(starttime)

            with open(monpath,"r") as infile:
                montemp = np.fromfile(infile,dtype=np.int32)

            moncount = np.sum(montemp)



            if time <= 0 or ((moncount/time < minmon or moncount/time>10*minmon) and minmon >0):
                continue

            mon += montemp

            with open(detpath,"rb") as infile:
                dettemp = np.fromfile(infile,count=-1)
                dettemp.tofile(outfile)
                del dettemp
    with open(path+"_bmon_histo.dat","wb") as stream:
        mon.tofile(stream)

