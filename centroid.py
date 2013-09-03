import reader
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime
from matplotlib import pyplot as plt

base_dir = "C:/userfiles/EXP011/SESAME_%i/SESAME_%i_"
XMLNS = "{http://neutrons.ornl.gov/SNS/DAS/runinfo_v4_3}"

def get_file(run):
    pel = reader.PelFile(base_dir%(run,run) + "neutron_event.dat")
    return pel.make3d()


def get_centroid(cube):
    height = np.sum(np.sum(cube,axis=1),axis=1)
    return np.sum(height*np.arange(128))/np.sum(height)

def get_dead(cube):
    all = np.sum(cube,axis=2)
    return(np.sum(all[:,[4,6]]))

def get_live(cube):
    all = np.sum(cube,axis=2)
    return(np.sum(all[:,[5,7]]))

def get_time(run):
    data_file = base_dir%(run,run) + "runinfo.xml"
    root = ET.parse(data_file).getroot()
    start = root.find(".//"+XMLNS+"StartTime").text.strip()
    stop = root.find(".//"+XMLNS+"StopTime").text.strip()

    format = "%Y-%m-%dT%H:%M:%S-04:00"
    start = datetime.strptime(start,format)
    stop = datetime.strptime(stop,format)

    return (stop,stop-start)

def get_monitor(run):
    mon_file = base_dir%(run,run) + "bmon_histo.dat"
    return np.sum(np.fromfile(mon_file,np.int32,-1))

def get_info(run):
    cube = get_file(run)

    cen = get_centroid(cube)

    mon = get_monitor(run)
    intensity = np.sum(cube)/mon
    dead = get_dead(cube)/mon
    live = get_live(cube)/mon

    end,length = get_time(run)
    
    del cube

    return (intensity,cen,mon,dead,live,end,length)

def save(start,stop):
    with open("C:/users/sesaadmin/Documents/run_history.dat","w") as outfile:
        outfile.write("Run\tIntensity\tMonitor\tCenter\tdead\tlive\t\time\length\n")
        for i in range(start,stop):
            int,cen,mon,dead,live,end,length = get_info(i)
            if mon > 8*10*60:
                outfile.write("%i\t%f\t%f\t%f\t%f\t%f\t%s\t%s\n"%
                              (i,int,mon,cen,dead,live,str(end),str(length))) 

def view(start,stop):
    time = []
    lengths = []
    mons = []
    intensities = []
    centers = []
    deads = []
    lives = []
    for i in range(start,stop):
        int,cen,mon,dead,live,end,length = get_info(i)
        if mon > 8*10*60:
            time.append(end)
            lengths.append(length)
            mons.append(mon)
            centers.append(cen)
            intensities.append(int)           
            deads.append(dead)
            lives.append(live)
    plt.plot_date(time,deads)
    plt.plot_date(time,lives)
    plt.show()
    deads = np.array(deads)
    lives = np.array(lives)
    boundary = np.where(deads>0.0)
    print(boundary)
    plt.plot_date(time,deads)
    plt.plot_date(time,lives,"r*")
    plt.show()
#    plt.plot_date(time,intensities)
#    plt.show()
#    plt.plot_date(time,centers)
#    plt.show()


if __name__ == "__main__":
#    save(67,274)
    view(67,274)

