import serial
import json
import time
import sys

import logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M",
                    filename="C:/MotorSoftware/motorlog.txt",
                    filemode="a")
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.WARN)
formatter = logging.Formatter("%(message)s")#The console just needs the message
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

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
#
    def save(self):
        status = {"a": self.a,
                  "aa": self.aa,
                  "ad": self.ad,
                  "ada": self.ada,
                  "v": self.v,
                  "loc": self.loc}
        with open(self.config,"w") as outfile:
            json.dump(status,outfile)
#
    def __del__(self):
        self.save()

topconfigs = ["slit1bottom.json",
              "slit1top.json",
              "slit1left.json",
              "slit1right.json",
              "slit2bottom.json",
              "slit2top.json",
              "slit2left.json",
              "slit2right.json"]

middleconfigs = ["dummy.json",
                 "dummy.json",
                 "dummy.json",
                 "rotation.json",
                 "goniox.json",
                 "gonioy.json",
                 "dummy.json",
                 "dummy.json"]

class Controller:
    """This class handles the motor controller, which can contrain up to eight motors"""
    def __init__(self,port,configs,timeout=0.25):
        self.ser = serial.Serial(port,timeout=timeout)
        self.ser.write("tlim\n")
        line = self.ser.readline()
        line = self.ser.readline()
        self.motors = [Motor(c) for c in configs]
        self.write("PSET " + ",".join([str(i.loc) for i in self.motors])+"\n")
    def go(self):
        motors = self.motors
        write=self.write
        write("DRIVE " + ''.join(['1' if i.active else 'X' for i in motors])+"\n")
        write("MA " + ''.join(['1' if i.active else 'X' for i in motors])+"\n")
        write("A " + ','.join([str(i.a) if i.active else '' for i in motors])+"\n")
        write("AD " + ','.join([str(i.ad) if i.active else '' for i in motors])+"\n")
        write("V " + ','.join([str(i.v) if i.active else '' for i in motors])+"\n")
        write("D " + ','.join([str(i.d) if i.active else '' for i in motors])+"\n")
        write("MC " + ''.join(['0' if i.active else 'X' for i in motors])+"\n")
        write("GO " + ''.join(['1' if i.active else '0' for i in motors])+"\n")
        write("DRIVE00000000\n")
        self.parseEncoder()
        for motor in motors:
            motor.d=0
            motor.active=False
        [motor.save() for motor in motors]     
    def write(self,command):
        time.sleep(0.1)
        ser = self.ser
        command = command.upper()
        logging.debug(command)
        ser.write(command)
        line = ser.readline()
        failures = 0
        while line.find(command) == -1 and failures < 5:
            logging.debug( "Wrote '"+command+"' and recieved '" + line + "'")
            line = ser.readline()
            failures += 1
        if failures >4:
            logging.error("Failed at command: %s"%command)
            return ""
        temp = ser.readline()
        #temp = ser.read(1000)
        ser.flush()
        return temp.split("\n>")[0]
    def writefile(self,file):
        with open(file,"r") as infile:
            lines = infile.readlines()
            for line in lines:
                self.write(line)
    def parseEncoder(self):
        self.ser.write("TPE\n")
        line = self.ser.readline()
        while line.find("TPE") == -1:
            logging.debug("Readback:"+line)#This is the echo back from the unit
            line = self.ser.readline()
        logging.debug("Line: "+line)
        response = self.ser.readline()
        failures = 0
        while response.find("TPE") == -1 and failures < 5:
            logging.debug("Readback:"+response)#This is the echo back from the unit
            response = self.ser.readline()
            failures += 1
        if failures > 4:
            logging.error("Recieved no response from Motor System")
            return self.parseEncoder() #Just try it again
        logging.debug("Response:"+response)
        #This is the response.  We use the readline to make sure that
        #we don't timeout.
        data = map(float,response.split("*TPE")[1].split(","))
        for (motor,place) in zip(self.motors,data):
            motor.loc = place 
    def __del__(self):
        self.ser.close()
    

class MotorFacade(object):
    def __init__(self):
        logging.info("Starting Top Controller")
        self.topcontroller = Controller(2,topconfigs,timeout=5)
        self.topcontroller.writefile("setuptop.txt")
        self.topcontroller.write("tlim\n")
        logging.info("Starting Middle Controller")
        self.middlecontroller = Controller(7,middleconfigs,timeout=5)
        logging.info("Writing to Middle Controller")
        self.middlecontroller.writefile("setupmiddle.txt")
        logging.info("Connecting to Middle Controller")
        self.middlecontroller.write("tlim\n")
        #Create motor getters
    #
        logging.info("Establishing getters and setters")
        topgetters = ["getT1","getB1","getL1","getR1","getT2","getB2","getL2","getR2"]
        topsetters = ["setT1","setB1","setL1","setR1","setT2","setB2","setL2","setR2"]
        for (i,g,s) in zip(range(8),topgetters,topsetters):
            setattr(self,g,self.getter(self.topcontroller,i))
            setattr(self,s,self.setter(self.topcontroller,i))
        middlemotors = ["dummy0","dummy1","dummy2","Rot","GonioX","GonioY","dummy6","dummy7"]
        for (i,name) in zip(range(8),middlemotors):
            setattr(self,"get"+name,self.getter(self.middlecontroller,i))
            setattr(self,"set"+name,self.setter(self.middlecontroller,i))
        logging.info("Initialization finished")
    
    
    def getter(self,controller,index):
        def newGetter():
            controller.parseEncoder()
            return controller.motors[index].loc
        return newGetter
    def setter(self,controller,index):
        def newSetter(n):
            logging.warn(n)
            controller.motors[index].active=True
            controller.motors[index].d=n
            controller.go()
            controller.parseEncoder()
            return controller.motors[index].loc
        return newSetter




from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

PORT = 7894

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("192.168.70.160", PORT),
                            requestHandler=RequestHandler)
server.register_introspection_functions()

server.register_instance(MotorFacade())
print("Registered")
server.serve_forever()
