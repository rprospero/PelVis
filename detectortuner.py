from reader import PelFile
import numpy as np
import os

def orthonorm(list):
    betas = []
    for a in list:
        u=a
        for x in betas:
            u -= x*np.inner(u,x)/np.inner(x,x)
        print(u)
        print(np.linalg.norm(u))
        betas.append(u)
    b = [x/np.linalg.norm(x) for x in betas]
    print(b)
    print("Orthonormed")
    return b

def project(data,basis):
    co = [] #coefficients
    for x in basis:
        co.append(np.inner(data,x))
    return co

if __name__ == "__main__":
    dir = "C:/Documents and Settings/adlwashi/My Documents/Variable Gains"
    files = ["11122009n.pel","11122009r.pel","11122009t.pel","11122009u.pel",
             "11122009y.pel","11132009c.pel","11132009g.pel"]
    files = [dir+"/"+file for file in files]
    data = PelFile()   
    ws = [data.getgains(data.peakheader(file)) for file in files]

    alphas = []
    for file in files[:2]:
        data = PelFile()
        data.readfileimage(file)
        alphas.append(data.make2d(0,0x7FFFFFFF).reshape(256*256))
    print(alphas)
    betas = orthonorm(alphas)
    perfect = np.ones(shape=(256*256),dtype=np.double)
#    perfect=perfect/np.linalg.norm(perfect)
#    print(perfect)
    co = project(perfect,betas)
    print(co)
    a = np.zeros(shape=(256*256),dtype=np.double)
    for i in range(len(co)):
        a += co[i]*betas[i]
        print(np.inner(betas[i],betas[i]))
















#    print(np.linalg.norm(a))
#    print(np.linalg.norm(perfect))

#    arr = [np.array([1.0,1.0,1.0]),np.array([1.0,2.0,3.0]),np.array([1.0,3.0,2.0]),np.array([1.0,0.0,0.0])]
#    print(orthonorm(arr))
    
#    files = os.listdir(dir)
#    files = [dir +"/"+ x for x in files]

#    ws = [(file,data.getgains(data.peakheader(file))) for file in files]
#    deltaws = []
#    for i in range(len(ws)-1):
#        deltaws.append((ws[i+1][0],ws[i+1][1]-ws[i][1]))
#    for i in range(19):
#        for d in deltaws:
#            if d[1][i] != 0 and d[1][19] != -505:
#                print((i,d[0],d[1]))

