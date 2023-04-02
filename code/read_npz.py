import numpy as np
import os, glob

path = os.path.abspath(os.getcwd())+'/data/' + '*.npz'

file_list = glob.glob(path)

print (file_list,path)

for each in file_list:
    
    print ("==============================================")
    
    temp = np.load(each)

    data = temp['data']

    print(data)