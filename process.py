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


if (len(sys.argv) < 1): 
	print ("Usage: \n ./process.py file_1 file_2 file_3 ...")

n_files = len(sys.argv) - 2
out_file_path = sys.argv[-1]

print ("Reading data from ", n_files, " files\n")


concentrations = []

frequencies = []
rs = []
thetas = []
for i in range(1, n_files+1):
	file_name = sys.argv[i]
	print("Reading from: " + file_name)
	freq_arr = []
	r_arr = []
	theta_arr = []
	with open (file_name) as fn: 
		read_csv = csv.reader(fn, delimiter = ',')  
		for row in read_csv:
			if (len( row) == 7): #header row with extra parameters
				# Extract the concentration
				conc_str = row[3]
				conc_matched = re.findall('[\d.]+', conc_str)
				conc = float(conc_matched[0])
				concentrations.append(conc)
			else:
				l = [int(x) for x in row]
				freq_arr.append(l[0])
				r_arr.append(l[1])
				theta_arr.append(l[2])		

		frequencies.append(freq_arr)
		rs.append(r_arr)
		thetas.append(theta_arr)


#Merge data
total_data = {}
for j in range(n_files): #Go through data from each file
	for i in range(len(frequencies[j])):
		f = frequencies[j][i]
		if ( f in total_data):
			total_data[f][j] = rs[j][i]
		else:
			total_data[f] = [0 for i in range(n_files)]
			total_data[f][j] = rs[j][i]


header_txt = ("freq, " + ', '.join([str(c) for c in concentrations]) + '\n')
print("Writing output: ", out_file_path)
if (os.path.exists(out_file_path)):
	print ("Error output file exists")
	exit()
out_file = open(out_file_path, 'w')
out_file.write(header_txt)
for f in total_data:
	out_file.write(str(f))
	out_file.write(',')
	out_file.write(','.join([str(x) for x in total_data[f]]))
	out_file.write('\n')
out_file.close()

