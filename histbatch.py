import __future__
from reader import PelFile
import glob
import numpy as np
import sys

files = glob.glob(sys.argv[1])
print(files)
files = [x for x in files if x[-3:]=="pel"]
for file in files:
    data = PelFile(file)
    hist = data.make3d()
    np.save(file+".npy",hist)
    print(file)
