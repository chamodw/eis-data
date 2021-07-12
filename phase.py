#!/usr/bin/env python3
import csv 
from datetime import datetime
import matplotlib.pyplot as plt 
import numpy as np
import os
import pandas as pd
import re
import serial
import struct
import sys 


def phase(r, i):
	return np.arctan(i/r)


if (len(sys.argv) < 1): 
	print ("Usage: \n ./process.py raw_file out_file")

in_file_path = sys.argv[1]
out_file_path = sys.argv[-1]


concentrations = []

frequencies = []
reals = []
ims = []
file_name = in_file_path
print("Reading from: " + file_name)

all_data = {}

header_rows = [] #header rows from the origina file containing vrange, gain etc
with open (file_name) as fn: 
	read_csv = csv.reader(fn, delimiter = ',')  


	
	for row in read_csv:
		if (len( row) > 4): #header rows
			header_rows.append(row)
			continue
		if ('freq' in row[0]):
			header_rows.append(row)
			continue
		else:
			l = [x for x in row]

			freq = int(l[0])
			r = int(l[1])
			im = int(l[2])
			current_conc =float( l[3])
			if (current_conc in all_data):
				all_data[current_conc][0].append(freq)
				all_data[current_conc][1].append(phase(r, im))
			else:
				all_data[current_conc] = [[],[],[]]
				all_data[current_conc][0].append(freq)
				all_data[current_conc][1].append(phase(r,im))

		




keys = sorted(all_data.keys())
print(keys)
if (os.path.exists(out_file_path)):
	print ("Error output file exists")
	exit()



out_file = open(out_file_path, 'w')

for r in header_rows: #write the original header rows to output file
	out_file.write(','.join(r))
	out_file.write('\n')

#write the csv header (freq, concentration1, concentration2...)
out_file.write(',freq,')
out_file.write(','.join([str(k) for k in keys]))
out_file.write('\n')

for fi in range(len(all_data[keys[0]][0])): #iterate through frequencies
	f = all_data[keys[0]][0][fi]
	out_file.write(','.join([str(fi), str(f)]))
	for k in keys:
		ph = all_data[k][1][fi]
		out_file.write(',')
		out_file.write('%0.3f' % ph)
	out_file.write('\n')
