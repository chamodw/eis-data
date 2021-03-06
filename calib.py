#!/usr/bin/env python3
import serial
import numpy as np
import sys
import struct
import matplotlib.pyplot as plt
from datetime import datetime



gain_factor = 1

v_range_names=['0', '2.0V', '1.0V', '400mV', '200mV']
v_range_values=[0, 0, 3, 2, 1];

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


def getPacket():
	s = struct.Struct("I I I I I I I I I I I");
	header=0xb5280013
	l=5
	footer=0x31a39b0e
	d=[header, l, 0,  start_freq, increment, num_increments,  0, num_avg, (v_range_values[v_range]<<8)+pga_gain, 0, footer];
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
	p = '='*int(i*80/n) + '-'*(80-int(i*80/n)) + '|'
	return p

# Print example usage if not enough arguments are provided 
if (len(sys.argv) < 3):
	printColor ("Usage calib.py port resistor frequency", 'r')
	exit()

port = sys.argv[1]
calib_res = float(sys.argv[2]) # Datafile output path
calib_freq = int(sys.argv[3])






try:
	ser = serial.Serial(port, timeout=100)
except:
	printColor("EIS Device not found", 'r')
	exit(1)

start_freq=calib_freq - 500
increment=10
num_increments=100
num_avg = 2

pga_gain = 1
v_range = 1

concentrations = [1, 2]
n_conc = len(concentrations)

print ("Start Frequency: ", start_freq/1000, "kHz")
print ("Frequency Increment: ", increment)
print ("Number of Increments: ", num_increments)

printColor("PGA Gain: " + str(pga_gain), 'g')
printColor("Voltage range: " + v_range_names[v_range] + " - " + str(v_range), 'g')

for i_conc in range(1):
#	conc = concentrations[i_conc] #current concentration
#	printColor(getProgressBar(i_conc+1, n_conc), 'g')

		#Create command packet for the sensor
	size, packet=getPacket()
	ser.write(packet); # Run the sensor
	printColor ("Starting data collection...", 'g')

	
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
		cur_freq = start_freq + increment*data_line[0]
		freq.append(cur_freq)

		data_line[0] = cur_freq; #write the calculate frequency back to array for easier string processing
		real.append(data_line[1])
		im.append(data_line[2])
		log_str = ','.join([str(x) for x in data_line])

		
#		out_file.write(log_str)
#		out_file.write("\n")

	print('\033[0m') # Reset terminal colors


	mag = [np.sqrt(real[x]**2+im[x]**2) for x in range(len(real))]

	i_mid = freq.index(calib_freq)
	calib_mag = mag[i_mid]
	gain_factor = (1/calib_mag)/calib_res;
	
	printColor("Gain factor = " + str(gain_factor) + ' # Res: ' + str(calib_res) + ', '  + str(calib_freq/1000) + 'kHz, range' + str(v_range)+ ", gain: " + str(pga_gain),  'g')

	plt.figure(1)
	plt.plot(freq, mag )
	plt.legend("ADC Magnitude with Rcal =  " + str(calib_res))
	plt.axline((calib_freq, calib_mag), slope=0)

	plt.pause(1)
	x = input()


