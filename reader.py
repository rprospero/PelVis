"""This module contains classes for reading PEL files

This module contains a single class: PelFile.  This class reads the header
information and neutron data saved in PEL files.  more information about
the format of these files can be found in the Lexitech PAPA Software Manual.

"""

import __future__

import struct
#import re
import numpy as np

from time import clock
from collections import namedtuple

def mapim(imarray):
    XDIM=8
    YDIM=256
    XDIMIM=16
    YDIMIM=128
    ZPAD=0
    maparray=[2, 15, 1, 16, 4, 13, 3, 14, 6, 11, 5, 12, 8, 9, 7, 10]
    newimarray=np.zeros((YDIMIM+ZPAD,XDIMIM))
    for i in range(len(maparray)):
        ti=maparray[i]
        if 0.5*ti!=int(0.5*ti):
           for j in range(YDIMIM):
                tj=j
                if ti<9:
                    newimarray[j+ZPAD,i]=imarray[YDIMIM-1-tj,(ti-1)/2]
                else:
                    newimarray[j,i]=imarray[YDIMIM-1-tj,(ti-1)/2]
        else:
            for j in range(YDIMIM):
                tj=j+YDIMIM
                if ti<9:
                    newimarray[j+ZPAD,i]=imarray[tj,ti/2-1]
                else:
                    newimarray[j,i]=imarray[tj,ti/2-1]
    return newimarray

class PelFile:
        """Handles the data stored in PEL files"""
        data = np.ndarray(shape=(0),dtype=np.int64)#Raw detector data

        def __init__(self,file=""):
		"""Create a PelFile"""
                if(file!=""):
                        self.readfileimage(file)
#		self.time=None
#		self.monitor=None

#         def loadmon(self,file):
#                 with open(file,"r") as infile:
#                         infile.readline() #drop first line
#                         line = infile.readline()
#                         m = re.search("lasted (\d+) milliseconds",line)
#                         if m:
#                                 self.time = m.group(1)
#                                 print(self.time)
#                 self.mon = np.loadtxt(file,dtype=np.int32,skiprows=3)
#                 print(self.mon)
                

        def parseHeader(self,bytes):
		"""Turn the Pel file header into structured data"""
                Header = namedtuple(
                        'Header',
                        "pel endian FileMajVer FileMinVer BytesPerSample " +
                        "SysHealth AppMajVer AppMinVer AppBetaVer LensPos " +
                        "DetectorName ProductNumber BitsPerCoord CanEnergy " +
                        "CanTime ADclockFrequ FirmMajVer FirmMinVer FirmBeta Serial " +
                        "AcquisitionMode CanAcqMode Shutter " +
                        "PAPAPowerSupplyVoltageCommand " +
                        "PAPAPowerSupplyVoltageCommandGain " +
                        "PAPAPowerSupplyVoltageCommandOffset " +
                        "PAPAPowerSupplyControlVoltageCommandGain " +
                        "PAPAPowerSupplyControlVoltageCommandOffset " +
                        "PAPAPowerSupplyVoltageEnable " +
                        "EnergyPowerSupplyVoltageCommand " +
                        "EnergyPowerSupplyVoltageCommandGain " +
                        "EnergyPowerSupplyVoltageCommandOffset " +
                        "EnergyPowerSupplyControlVoltageCommandGain " +
                        "EnergyPowerSupplyControlVoltageCommandOffset " +
                        "EnergyPowerSupplyVoltageEnable " +
                        "MCPPowerSupplyVoltageCommand " +
                        "MCPPowerSupplyVoltageCommandGain " +
                        "MCPPowerSupplyVoltageCommandOffset " +
                        "MCPPowerSupplyControlVoltageCommandGain " +
                        "MCPPowerSupplyControlVoltageCommandOffset " +
                        "MCPPowerSupplyVoltageEnable " +
                        "x1Gain x2Gain x3Gain x4Gain x5Gain x6Gain x7Gain x8Gain x9Gain x10Gain " +
                        "y1Gain y2Gain y3Gain y4Gain y5Gain y6Gain y7Gain y8Gain y9Gain y10Gain " +
                        "strobeGain EnergyGain ThresholdGain "+
                        "ADVoltageOffset ADAOffset ADBOffset ADCOffset ADDOffset "+
                        "StrobeTriggerMin StrobeTriggerMax StrobeEndEventFrac " +
                        "EnergyTriggerMin EnergyTriggerMax EnergyEndEventFrac " +
                        "ADAFillSampleIntervalLength ADDFillSampleIntervalLength " +
                        "GateCapturePolarity TimerResetEdgePolarity " +
                        "LeadTimer LagTimer Gray BitShift " +
                        "TemperatureSetPoint1 TemperatureSetPoint2 " +
                        "KP1 KP2 KI1 KI2 KD1 KD2 Temperature1 Temperature2 " +
                        "StrobePulseWidth " +
                        "Year Month Day Hour Minute Second")


                format = "4s" #header
                format += " ?" #endian  Note that this is currently ignored
                (pelstring,endian) = struct.unpack(format,bytes[0:5])
#                if pelstring != ".pel": raise Exception("Not a pel file")
                if endian:
                        format = ">" #big endian
                else:
                        format = "<" #little endian
                format += "4s ?" #header and endian
                format += "B" #Major version
                format += "B" #Minor Version
                format += "B" #Bytes per sample
                format += "B" #System Health
                format += "B" #Application Software Major Version
                format += "B" #Application Software Minor Version
                format += "B" #Application Software Beta Version
                format += "H" #Lens focus position
                format += " 40s " # Detector Name
                format += "H" # Product Number
                format += "B" # Bits per coordinate
                format += "B" #Detector Energy Capability
                format += "B" #Detector Timing Capability
                format += "H" #AD Clock Frequency
                format += "B" #Firmware Major Version
                format += "B" #Firmware Minor Version
                format += "B" #Firmware Beta Version
                format += "H" #Serial Number
                format += "B" #Acquisition Mode
                format += "I" #Acquisition Mode Capability
                format += "B" #Shutter State
                format += "H" #PAPA PMT power supply voltage command
                format += "H" #PAPA PMT power supply voltage gain
                format += "H" #PAPA PMT power supply voltage command offset
                format += "H" #PAPA PMT power supply control voltage command gain
                format += "H" #PAPA PMT power supply control voltage command offsert
                format += "B" #PAPA PMT power supply voltage enable

                format += "H" #Energy PMT power supply voltage command
                format += "H" #Energy PMT power supply voltage gain
                format += "H" #Energy PMT power supply voltage command offset
                format += "H" #Energy PMT power supply control voltage command gain
                format += "H" #Energy PMT power supply control voltage command offsert
                format += "B" #Energy PMT power supply voltage enable
                format += "H" #Intensifier MCP power supply voltage command
                format += "H" #Intensifier MCP power supply voltage gain
                format += "H" #Intensifier MCP power supply voltage command offset
                format += "H" #Intensifier MCP power supply control voltage command gain
                format += "H" #Intensifier MCP power supply control voltage command offsert
                format += "B" #Intensifier MCP power supply voltage enable
                format += " 10H " #X Channel gains
                format += " 10H " #Y Channel gains
                format += "H" #Strobe PMT Channel Gain
                format += "H" #Energy PMT Channel Gain
                format += "H" #Threshold Channel Gain
                format += "H" #AD Voltage Offset
                format += "H" #AD Channel A Offset
                format += "H" #AD Channel B Offset
                format += "H" #AD Channel C Offset
                format += "H" #AD Channel D Offset
                format += "H" #PAPA Strobe Trigger min
                format += "H" #PAPA Strobe Trigger max
                format += "H" #PAPA Strobe end event fraction
                format += "H" #Energy Trigger min
                format += "H" #Energy Trigger max
                format += "H" #Energy end event fraction
                format += "B" #AD A filter sample interval length
                format += "B" #AD D filter sample interval length
                format += "B" #Gate Capture Polarity
                format += "B" #Timer reset edge Polarity
                format += "H" #Coincidence lead timer
                format += "H" #Coincidence lag timer
                format += "B" #Gray to binary conversion adder
                format += "B" #Binary big shift
                format += " 2H " #Zone temperature set point
                format += " 2H " #Zone KP Gain
                format += " 2H " #Zone KI Gain
                format += " 2H " #Zone KD Gain
                format += " 2H " #Zone temperature
                format += "H" #strobe pulse width
                format += "39x" #unused
                format += "H" #Year
                format += "H" #Month
                format += "H" #Day
                format += "H" #Hour
                format += "H" #Minute
                format += "H" #Second
                header = Header._make(struct.unpack(format,bytes))
                return header

        #Remember to use in-place operations to save on memory overhead
        def convertTime(self,timearr):
		"""Convert an array of TOF data into neutron wavelengths."""
                #convert timearr into microseconds
                timearr *= 0.1 #Convert to microseconds
                #convert timearr into wavelength
                distanceToG4 = 3.7338+2.5297
                distanceToDetector = 3.6 #FIXME
                timearr -= 860
                timearr *= 3.956034e-7/(distanceToDetector+distanceToG4)/1e-10*1e-6*10 #The last 10 is to handle fractional angstroms
                return timearr

        def make3d(self):
		"""Make a 3D histogram from the raw data."""
                print("Cubing Image")
                start=clock()                
                statusfunc = self.statusfunc
                l = len(self.data)
                sd =self.data
                i=0;

                cube = np.zeros([128,16,200],dtype=np.float32)

		#If there's no data, return an empty array
                if l==0:
                        return cube

                Z = self.data[1::2] & 0xFFFF#position data

                timearr = self.convertTime(np.asarray(self.data[0::2],dtype=np.float64))#time data
                timearr = np.asarray(np.floor(timearr),np.uint16)
                
		#Loop over 20 angstroms in steps of 0.1 angstroms
		np.seterr(over='raise')

		for i in range(200):
			place = np.where(timearr==i)
			if len(place[0]) > 0:
				temp,_ = np.histogram(Z[place],bins = np.arange(8*256+1))
				temp = temp.reshape(256,8,order="F")
				cube[:,:,i] = mapim(temp)[::-1,:]
			statusfunc(i*5.0)
				

                stop=clock()
                del timearr

                print((stop-start))                        
                return cube

        
        def spectrum(self,output):
		"""Save the neutron spectrum to a text file"""
                with open(output,'w') as of:
                        timearr = (self.data >> 32) & 0x7FFFFFFF
                        timearr = self.convertTime(timearr)
                        timearr /= 10

			#Get the spectrum and wavelengths
                        (spec,lmbda) = np.histogram(timearr,bins=np.arange(2.0,50.0,0.1))
                        hist = np.column_stack((lmbda[1:],spec))
                        for point in hist:
                                of.write("%f %i\n" % (point[0],point[1]))
                        of.close()
                        return (spec,lmbda)
                

        def statusfunc(self,x):
		"""Status update function

		This function is called to tell other program components
		the progress in loading the PelFile.  The progress is given
		on a scale of 0 to 1000.  This function should be overwritten
		by whatever function is loading the pel file to do what it
		needs with the load time information.

		"""
                return

        def getgains(self,h):
		"""Pulls the PMT gains information into a numpy array"""
                return np.array([h.x1Gain,h.x2Gain,h.x3Gain,h.x4Gain,h.x5Gain,h.x6Gain,h.x7Gain,h.x8Gain,h.x9Gain,h.x10Gain,
                        h.y1Gain,h.y2Gain,h.y3Gain,h.y4Gain,h.y5Gain,h.y6Gain,h.y7Gain,h.y8Gain,h.y9Gain,h.y10Gain],np.double)

        def readfileimage(self,path):
		"""Reads a raw Pel File into memory."""
                print("Loading PEL file"+path)
                start=clock()
                statusfunc = self.statusfunc
                with open(path,"rb") as infile:
                    #self.header = self.parseHeader(infile.read(256))
		    #Raw File has no header
                    #point = infile.read(8)
                    self.data = np.fromfile(infile,np.int32,-1)
                infile.close()
                stop=clock()
                print((stop-start))

	def make1d(self,mins,maxs):
                """Make a 1D histogram from the spectrum data."""

		xmin,ymin = mins
		xmax,ymax = maxs
		c = self.make3d()[ymin:ymax,xmin:xmax]
		return np.sum(np.sum(c,axis=0,dtype=np.float64()),axis=0)
		

if __name__=="__main__":
        data = PelFile()
        
        data.readfileimage("C:/Documents and Settings/adlwashi/Desktop/20091102101415-AM12.pel")
        print("Read File")
        data.spectrum("spectrum.txt")
        #print("Reverse Grey")
        #data.reverseGrey()
        #temp = set([data.fullGrayCode(i) for i in range(512)])
        #for i in temp:
        #        print "%03o" % i
        #print(len(temp))
