#!/usr/bin/env python3
import serial
import numpy as np
import sys
import struct
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd



gain_factor =   1.0157660024619305e-08 # Res: 22060.0, 30.0kHz, range1, gain: 1
#5.374746845316806e-08 # Res: 22060.0, 30.0kHz, range3, gain: 1

#2.2117844010575636e-08 # Res: 10000.0, 30.0kHz, range2, gain: 1
#2.1971215977298026e-08 # Res: 22060.0, 30.0kHz, range2, gain: 1
#1.0202707065678497e-07 # Res: 22060.0, 30.0kHz 
#1.0183365488980382e-09 # Res: 120500.0

v_range_names=['0', '2.0V', '1.0V', '400mV', '200mV']

#Generates command packet for EIS Device
#  Returns a tuple (size, packed_byte_structure)

# +- Header
# +- length 
# +- 0
# +- Start Frequency
# +- Increment frequency
# +- Number of increments
# +- Resistance
# +- Averaging count 
# +- 0
# +- 0
# +- Footer

#datastructures to hold all the data
session_freq = []
session_data_mag = []
session_data_phase = []


def main():

# Print example usage if not enough arguments are provided 
	if (len(sys.argv) < 2):
		printColor ("Usage hw_test.py port ", 'r')
		exit()

	port = sys.argv[1]



	try:
		ser = serial.Serial(port, timeout=100)
	except:
		printColor("EIS Device not found", 'r')
		exit(1)

	
#Fixed parameters
	start_freq=10000
	increment = 400
	num_increments=200
	num_avg = 1
	v_range = 1
	pga_gain = 1

	n_conc = 2


	print ("Start Frequency: ", start_freq/1000, "kHz")
	print ("Frequency Increment: ", increment)
	print ("Number of Increments: ", num_increments)
	print ("Gain factor = " + str(gain_factor) )
	printColor("PGA Gain: " + str(pga_gain), 'g')
	printColor("Voltage range: " + v_range_names[v_range] + " - " + str(v_range), 'g')

# Define file headers that include the parameters
		# Populate the freqency list

	# Loop through each of the concentrations 
	for i_conc in range(n_conc):
		conc = i_conc


		#Print the progress 
		print(getProgressBar(i_conc, n_conc))

		# Announce the next concentration in the line up
		printColor ('*** ' + str(conc) + ' ***', 'g')	
		x = input("Press enter to collect data")

			
		# Command the hardware to perform a sweep and retrieve the data
		(freq, real, im) = performSweep(ser, start_freq = start_freq, increment_freq = increment, 
								num_increments = num_increments, num_avg = num_avg, 
									v_range = v_range, pga_gain = pga_gain)
		impedance = impedancePhase(real, im)






		
		print ("Real range : " + str( min(real)) + " - " + str(max(real))), 	
		print ("Imaginary range : " + str( min(im)) + " - " + str(max(im))), 	
		plt.figure(1)
		plt.plot(freq, impedance, label = str(conc))
#		plt.ylim(bottom = 0)
		plt.legend()
		plt.pause(1)

	x = input("Press enter to save data, type x to discard ")


def getPacket( start_freq, increment_freq, num_increments, num_avg, v_range, pga_gain):
	v_range_values=[0, 0, 3, 2, 1];
	s = struct.Struct("I I I I I I I I I I I");
	header=0xb5280013
	l=5
	footer=0x31a39b0e
	d=[header, l, 0,  start_freq, increment_freq, num_increments,  0, num_avg, (v_range_values[v_range]<<8)+pga_gain, 0, footer];
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

# Generates a fancy progress bar
# Parameters (progress_count, full_count)
# Returns a string
def getProgressBar (i, n):
	i = i+1
	fill = '█'
	l = 60
	blank = '-'
	f = int(i*l/n)
	e = l-int(i*l/n)
	p = fill*f + blank*e + '|' + " " + str(i) + "/" + str(n)
	
	return p



def performSweep(ser,  start_freq, increment_freq, num_increments, num_avg, v_range, pga_gain):
	size, packet=getPacket(start_freq = start_freq, increment_freq = increment_freq, 
								num_increments = num_increments, num_avg = num_avg, 
									v_range = v_range, pga_gain = pga_gain)
	ser.write(packet); # Run the sensor

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
		data_line = [int(x) for x in line.decode('utf-8').split(',')]
		cur_freq = start_freq + increment_freq*data_line[0]
		freq.append(cur_freq)

		data_line[0] = cur_freq; #write the calculate frequency back to array for easier string processing
		real.append(data_line[1])
		im.append(data_line[2])


	print('\033[0m') # Reset terminal colors
	return (freq, real, im)


def impedancePhase(real, im):
	adcMag = [np.sqrt(real[x]**2+im[x]**2) for x in range(len(real))]
	impedanceMag = [1/(gain_factor*m) for m in adcMag]
	return impedanceMag



main()
