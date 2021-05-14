#!/usr/bin/env python3
import serial
import numpy as np
import sys
import struct
import matplotlib.pyplot as plt
from datetime import datetime


if (len(sys.argv) < 3):
	print ("Usage comm.py port data_directory sample_id")

port = sys.argv[1]
path = sys.argv[2]



def getPacket():
	s = struct.Struct("I I I I I I I I I I I");
	header=0xb5280013
	l=3
	footer=0x31a39b0e
	d=[header, l, 0,  start_freq, increment, num_increments,  0, 0, 0, 0, footer];
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


try:
	ser = serial.Serial(port, timeout=1)
except:
	printColor("EIS Device not found", 'r')
	exit(1)

start_freq=10000
increment=1000
num_increments=100
sample_id=sys.argv[3]



while(1):
	print(sample_id, " : ", start_freq, increment, num_increments);
	print ("Sample ID: ", sample_id);
	print ("Start Frequency: ", start_freq/1000, "kHz")
	print ("Frequency Increment: ", increment)
	print ("Number of Increments: ", num_increments)
	print("Enter details to change, or enter to continue collecting data")
	inp = input()
	if (len(inp)):
		l = inp.split(',');
		sample_id = l[0]
		start_freq = int(l[1]);
		increment = int(l[2]);
		num_increments = int(l[3]);
		print(sample_id, " : ", start_freq, increment, num_increments);

	#Create command packet for the sensor
	size, packet=getPacket()
	ser.write(packet); # Run the sensor
	printColor ("Starting data collection...", 'g')



	#Open file for data recording
	now=datetime.now()
	time_str=now.strftime("%Y%m%d-%H:%M")
	out_file=open(path + '/' + time_str + '.txt', 'w');

	#record the parameters
	header_line = ",,," + sample_id + "," + str(start_freq) + "," + str(increment) + "," + str(num_increments)
	out_file.write(header_line)
	out_file.write("\n")
		
	real = []
	im = []
	freq =  []

	print('\033[0;33m')
	for i in range(num_increments):
		line = ser.readline(100);

		# Fancy progress bad animation
		print('-'*int(i*80/num_increments) + ' '*(80-int(i*80/num_increments)) + '|', end='\r')

		if (line == b''):
			continue
		data_line = [int(x) for x in line.decode('utf-8').split(',')]
		cur_freq = start_freq + increment*data_line[0]
		freq.append(cur_freq)

		data_line[0] = cur_freq; #write the calculate frequency back to array for easier string processing
		real.append(data_line[1])
		im.append(data_line[2])
		log_str = ','.join([str(x) for x in data_line])
		out_file.write(log_str)
		out_file.write("\n")

	
	plt.plot(freq, real, label = 'Real')
	plt.plot(freq, im)
	plt.xlabel("Frequency")
	plt.show()


	#Attempt plolar plot
	try:
		r = [np.sqrt(real[i]**2+im[i]**2) for i in range(len(real))]
		theta = [np.arctan(im[i]/real[i]) for i in range(len(real))]
		plt.polar(theta, r)
		plt.show()
	except:
		printColor("Polar plot failed", 'r')


	out_file.close()
	printColor("\nData writeen to " + out_file.name, 'g')
	exit()
