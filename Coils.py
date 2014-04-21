"""This module handles controlling the current through the solenoids

This code was written to talk with a custom labview server on the
current control computer.  Note that, currently, the server does
not respond with the current currents.  When you first load the
module, you should set all of the current values to synchronize
with the server.

"""

import __future__
import xmlrpclib

class Coils():
    """This object manages the connection to the current control server"""
    HOST = "http://192.168.62.160"#IP address for the server
    PORT="7892"#port number for the server
    P = None

    def __init__(self):
        """Creates the connection object"""
        self.__dict__["P"] = xmlrpclib.ServerProxy(self.HOST+":"+self.PORT, allow_none = True)

    def Set(self,curr,coil):
        self.P.Set(curr,coil)
        return self.P.Read(coil)

    def Read(self,coil):
        return self.P.Read(coil)

    def __getattr__(self,field):
        print field
        return self.Read(field)

    def __setattr__(self,field,value):
        self.Set(value,field)


if __name__=="__main__":
    coils = Coils()
    coils.Set(2,1)
    
