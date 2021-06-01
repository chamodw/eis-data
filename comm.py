#!/usr/bin/env python3
import serial
import numpy as np
import sys
import struct
import matplotlib.pyplot as plt
from datetime import datetime



gain_factor = 1

def getPacket():
	s = struct.Struct("I I I I I I I I I I I");
	header=0xb5280013
	l=3
	footer=0x31a39b0e
	d=[header, l, 0,  start_freq, increment, num_increments,  0, num_avg, 0, 0, footer];
	packed_data=s.pack(*d);
	return (s.size, packed_data)

def printColor(text, color):
	prefix = ""
	suffix = "\033[0m"
	if (color == 'r'):
		prefix = "\033[0;31m"
	elif (color == 'g'):
		prefix = "\033[0;32m"
	
	print (prefix+text+suffix)

def getProgressBar (i, n):
	p = '='*int(i*80/n) + '-'*(80-int(i*80/n)) + '|'
	return p

if (len(sys.argv) < 3):
	printColor ("Usage comm.py port data_directory sample_id", 'r')
	exit()

port = sys.argv[1]
path = sys.argv[2]






try:
	ser = serial.Serial(port, timeout=100)
except:
	printColor("EIS Device not found", 'r')
	exit(1)

start_freq=1000
increment=10
num_increments=100
num_avg = 4
#
#print ("Enter session id (solution_electrode)")
#session_id = input()
#print ("Enter temperature")
#temperature = input()
#print ("Enter concentrations, separated by commas")
#s = input()
#concentrations = [float(x) for x in s.split(',')]
#
session_id = 'avg2'
temperature = 25
concentrations = [1, 2]
n_conc = len(concentrations)

print ("Session ID: ", session_id);
print ("Start Frequency: ", start_freq/1000, "kHz")
print ("Frequency Increment: ", increment)
print ("Number of Increments: ", num_increments)
for i_conc in range(n_conc):
#	conc = concentrations[i_conc] #current concentration
#	printColor(getProgressBar(i_conc+1, n_conc), 'g')

		#Create command packet for the sensor
	size, packet=getPacket()
	ser.write(packet); # Run the sensor
	printColor ("Starting data collection...", 'g')



#	#Open file for data recording
#	now=datetime.now()
#	out_file=open(path + '/' + session_id + '_' + str(concentrations[i_conc]) +  '.txt', 'w');
#
#	#record the parameters
#	header_line = ",,," + session_id + ',' + str(conc) 
#	out_file.write(header_line)
#	out_file.write("\n")
		
	real = []
	im = []
	freq =  []

	print('\033[0;33m')
	for i in range(num_increments):
		line = ser.readline(100);

		# Fancy progress bad animation
		print(getProgressBar(i, num_increments), end='\r')

		if (line == b''):
			continue
		print (line)
		data_line = [int(x) for x in line.decode('utf-8').split(',')]
		cur_freq = start_freq + increment*data_line[0]
		freq.append(cur_freq)

		data_line[0] = cur_freq; #write the calculate frequency back to array for easier string processing
		real.append(data_line[1])
		im.append(data_line[2])
		log_str = ','.join([str(x) for x in data_line])
#		out_file.write(log_str)
#		out_file.write("\n")
	print (real)
	plt.figure(1)
	plt.plot(freq[1:], real[1:], label = 'Real')
	plt.plot(freq[1:], im[1:], label = 'imag')
	plt.pause(1)
#	x = input()
#	ax.plot(freq[1:], im[1:])

#	#Attempt plolar plot
#	try:
#		r = [np.sqrt(real[i]**2+im[i]**2) for i in range(len(real))]
#		theta = [np.arctan(im[i]/real[i]) for i in range(len(real))]
#		plt.polar(theta[1:], r[1:])
#		plt.show()
#	except:
#		printColor("Polar plot failed", 'r')
#
#
	continue
	out_file.close()
	printColor("\nData writeen to " + out_file.name, 'g')

