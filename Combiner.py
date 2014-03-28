import xml.etree.ElementTree as ET
import HTMLParser
import json
import numpy as np
import os.path
from time import strptime,mktime
from math import floor,sqrt

XMLNS = "{http://neutrons.ornl.gov/SNS/DAS/runinfo_v4_3}"

def load(paths,filter=None):
    currents = set([])#List of the configurations of the instrument
    runsets = {}#Directionary of lists of run nodes, indexed by their instrument configuration

    for path in paths:
        print(path)
        base = os.path.dirname(path)
        text = ET.parse(path).getroot().find(".//"+XMLNS+"Notes").text 
        text = HTMLParser.HTMLParser().unescape(text)
        manifest = json.loads(text)
        
##        if ((filter is not None) and 
##            (floor(float(manifest['triangle1'])) != filter)):
##            continue #wrong triangle current
        try:
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
        except:
            print("Could not retrieve currents for run " + str(base[-5:]))
            continue
        if current in currents:
            runsets[current].append(path)
        else:
            currents.add(current)
            runsets[current]=[path]
    return runsets

def save(path,minmon,keys,runsets):
    runs = [x for key in keys for x in runsets[key]]
    mon = np.zeros((50001,),dtype=np.int32)
    tottime = 0
    detcount=0
    format1 = "%Y-%m-%dT%H:%M:%S-04:00"
    format2 = "%Y-%m-%dT%H:%M:%S-04:00-04:00"
    with open(path+"_neutron_event.dat","wb") as outfile:
        for r in runs:
            monpath = r[:-11] + "bmon_histo.dat"
            detpath = r[:-11] + "neutron_event.dat"
            starttime = strptime(ET.parse(r).getroot().find(".//"+XMLNS+"StartTime").text.strip(),format1)
            stoptime = strptime(ET.parse(r).getroot().find(".//"+XMLNS+"StopTime").text.strip(),format2)

            time = mktime(stoptime)-mktime(starttime)

            with open(monpath,"r") as infile:
                montemp = np.fromfile(infile,dtype=np.int32)

            moncount = 1.*np.sum(montemp)
            print "Run number: " + str(r[-17:-12])
            print "Time: " + str(time)


            #Fixed for enabling dead run substraction 04/01/2013 done by Radian 
            if time <= 0 or ((moncount/time < minmon-20 or \
                              moncount/time>minmon+20) and minmon >0):
                print ":::: SKIPPING RUN: " + str(r[-17:-12]) + " ::::\n"
                print moncount/time
                print time
                continue

            print "Monitor counts: " + str(moncount)
            print "Monitor count rate: " + str(round(moncount/time,2))

            mon += montemp
            tottime += time

            with open(detpath,"rb") as infile:
                dettemp = np.fromfile(infile,count=-1)
                dc = 1.*len(dettemp)
                dcr = round(dc/moncount,2)
                dcrerr = sqrt(dc/(moncount**2) + (dc**2)/(moncount**3))
                print "Detector counts: " + str(dc)
                print "Detector count rate: " + str(round(dc/time,2))
                print "Detector counts/Monitor counts: " + str(dcr) + \
                      " +/- " + str(dcrerr) + "\n"
                if dcr <= 0:# or dcrerr/dcr > 0.02:
                    print "#### SKIPPING RUN: " + str(r[-17:-12]) + " ####\n"
                    mon -= montemp
                    continue
                detcount += len(dettemp)
                dettemp.tofile(outfile)
                del dettemp
    with open(path+"_bmon_histo.dat","wb") as stream:
        mon.tofile(stream)
    print "Total Monitor Counts = " + str(np.sum(mon))
    print "Total Detector Counts = " + str(detcount)
    print "Total Time = " + str(tottime)
    if tottime > 0:
        print "Monitor Count Rate = " + str(np.sum(mon)/tottime)
        print "Detector Count Rate = " + str(detcount/tottime)
