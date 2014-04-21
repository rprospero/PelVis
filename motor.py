import serial
import json
import time
import sys

class Motor:
    """This class handles the movement of a single motor"""
    def __init__(self,config):
        self.config = config
        with open(config,"r") as infile:
            data = json.load(infile)

            self.a = float(data["a"]) #Acceleration
            self.aa = float(data["aa"]) #Average Acceleration
            self.ad = float(data["ad"]) #Deceleration
            self.ada = float(data["ada"]) #Average Deceleration
            self.v = float(data["v"]) #Velocity
            self.d = 0 #Displacement
            self.loc = float(data["loc"]) #Location
            self.active=False

    def hardset(self,location):
        self.loc = location

    def save(self):
        status = {"a": self.a,
                  "aa": self.aa,
                  "ad": self.ad,
                  "ada": self.ada,
                  "v": self.v,
                  "loc": self.loc}
        with open(self.config,"w") as outfile:
            json.dump(status,outfile)

    def __del__(self):
        self.save()


configs = ["slitbottom.json",
           "slitleft.json",
           "slittop.json",
           "slitright.json",
           "dummy.json",
           "dummy.json",
           "zaxis.json",
           "dummy.json"]

class Controller:
    """This class handles the motor controller, which can contrain up to eight motors"""
    def __init__(self,port,timeout=0.25):
        self.ser = serial.Serial(port,timeout=0.25)
        self.ser.write("tlim\n")

        line = self.ser.readline()
        line = self.ser.readline()
        
        self.motors = [Motor(c) for c in configs]

    def go(self):
        motors = self.motors
        write=self.write
        write("DRIVE " + ''.join(['1' if i.active else 'X' for i in motors])+"\n")
        write("MA " + ''.join(['0' if i.active else 'X' for i in motors])+"\n")
        write("A " + ','.join([str(i.a) if i.active else '' for i in motors])+"\n")
        #write("AA " + ','.join([str(i.aa) if i.active else '' for i in motors])+"\n")
        write("AD " + ','.join([str(i.ad) if i.active else '' for i in motors])+"\n")
        #write("ADA " + ','.join([str(i.ada) if i.active else '' for i in motors])+"\n")

        write("V " + ','.join([str(i.v) if i.active else '' for i in motors])+"\n")
        #write("TLIM\n")
        #write("V 1,,,,,,,\n")

        print("D " + ','.join([str(i.d) if i.active else '' for i in motors])+"\n")

        write("D " + ','.join([str(i.d) if i.active else '' for i in motors])+"\n")
        write("MC " + ''.join(['0' if i.active else 'X' for i in motors])+"\n")
        write("GO " + ''.join(['1' if i.active else '0' for i in motors])+"\n")
        write("DRIVE00000000\n")

        self.parseEncoder()
        [motor.save() for motor in motors]
        

    def write(self,command):
        ser = self.ser
        command = command.upper()
        print(command)
        ser.write(command)
        line = ser.readline()
        while line.find(command) == -1:
            print "Wrote '"+command+"' and recieved '" + line + "'"
            line = ser.readline()
        temp = ser.readline()
        #temp = ser.read(1000)
        ser.flush()
        return temp.split("\n>")[0]

    def writefile(self,file):
        with open(file,"r") as infile:
            lines = infile.readlines()
            for line in lines:
                sys.stdout.write(self.write(line))
            sys.stdout.flush()

    def parseEncoder(self):
        #response = self.write("TPE\n")
        #print(response)
        self.ser.write("TPE\n")
        line = self.ser.readline()
        while line.find("TPE") == -1:
            print("Readback:"+line)#This is the echo back from the unit
            line = self.ser.readline()
        print("Line: "+line)
        response = self.ser.readline()
        while response.find("TPE") == -1:
            print("Readback:"+response)#This is the echo back from the unit
            response = self.ser.readline()
        print("Response:"+response)
        #This is the response.  We use the readline to make sure that
        #we don't timeout.
        data = map(float,response.split("*TPE")[1].split(","))
        for (motor,place) in zip(self.motors,data):
            motor.loc = place 
        print(data)
        

    def __del__(self):
        self.ser.close()

def test(n):
    con = Controller(7,timeout=None)
    print([motor.loc for motor in con.motors])
    con.writefile("setupmiddle.txt")
    con.write("tlim\n")
    print(con.write("TPC\n"))
    print(con.write("TPE\n"))
    con.motors[6].active=True
    con.motors[6].d=n
    #con.motors[2].active=True
    #con.motors[2].d=n

    time.sleep(8)
    con.go()
    print([motor.loc for motor in con.motors])

    #time.sleep(8)
    print(con.write("TLIM\n"))
    print(con.write("TPC\n"))
    print(con.write("TPE\n"))
    del con

print("Reloaded")
