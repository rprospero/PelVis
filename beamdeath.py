from reader import PelFile
from monfile import MonFile
import numpy as np
import matplotlib.pyplot as plt

from optparse import OptionParser
import os

basedir = "C:/userfiles/EXP012/"

if __name__=='__main__':

    parser = OptionParser(usage="beamdeath.py firstrun lastrun\n" \
                          "Displays a graph of the total detector counts " \
                          "versus run number.\n" \
                          "Then attempts to display polarization by assuming " \
                          "that adjoining runs are in alternate flipping states."   )

    (options,runs) = parser.parse_args()

    print int(runs[0])
    print int(runs[1])
    runs = np.arange(int(runs[0]),int(runs[1]))

    data = [PelFile(basedir+"SESAME_%i/SESAME_%i_neutron_event.dat"%(r,r))
            for r in runs]

    data = np.asarray([len(p.data)/2 for p in data])

    plt.title("Counts Versus Time")
    plt.xlabel("Run Number")
    plt.ylabel("Total Detector Counts")
    plt.plot(runs,data)
    plt.show()

    u = np.array(data[0::2],dtype=np.float64)
    d = np.array(data[1::2],dtype=np.float64)
    if len(u) > len(d):
        u = u[:-1]
    p = (u-d)/(u+d)
    if np.max(p) < 0:
        p *= -1
    plt.title("Crude Polarization")
    plt.xlabel("Run Number")
    plt.ylabel("Polarization")
    plt.plot(runs[1::2],p)
    plt.show()
