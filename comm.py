#!/usr/bin/env python3
import serial
import numpy as np
import sys
import struct
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd



gain_factor = 7.128300377252934e-09 # Res: 22060.0, 70.0kHz, range1, gain: 1
#1.0092016396570935e-08 # Res: 22060.0, 30.0kHz, range1, gain: 1
#1.0126858710209283e-08 # Res: 22060.0, 6.0kHz, range1, gain: 1
#1.0092016396570935e-08 # Res: 22060.0, 30.0kHz, range1, gain: 1
#1.0157660024619305e-08 # Res: 22060.0, 30.0kHz, range1, gain: 1
#5.374746845316806e-08 # Res: 22060.0, 30.0kHz, range3, gain: 1

#2.2117844010575636e-08 # Res: 10000.0, 30.0kHz, range2, gain: 1
#4.89239538969537e-09 # Res: 10000.0, 30.0kHz
 

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
	if (len(sys.argv) < 3):
		printColor ("Usage comm.py port data_directory sample_id", 'r')
		exit()

	port = sys.argv[1]
	path = sys.argv[2] # Datafile output path



	try:
		ser = serial.Serial(port, timeout=100)
	except:
		printColor("EIS Device not found", 'r')
		exit(1)

	
#Fixed parameters
	start_freq=60000
	increment = 40
	num_increments= 500
	num_avg = 4
	v_range = 1
	pga_gain = 1


#User parameters
	session_id = input("Enter session ID: ")
	temperature = float(input("Enter temperature: "))
	conc_str = input("Enter concentrations separated by spaces: ")
	concentrations = [float(x) for x in conc_str.split(' ')]
	n_conc = len(concentrations)

	print ("Start Frequency: ", start_freq/1000, "kHz")
	print ("Frequency Increment: ", increment)
	print ("Number of Increments: ", num_increments)
	print ("Temperature: ", temperature)
	print ("Gain factor = " + str(gain_factor) )
	printColor("PGA Gain: " + str(pga_gain), 'g')
	printColor("Voltage range: " + v_range_names[v_range] + " - " + str(v_range), 'g')

# Define file headers that include the parameters
	file_header_1 = "#, session_id, temperature, start_freq, increment, num_increments, num_avg, v_range, pga_gain, gain_factor\n"	
	file_header_2 = '#' + ','.join([session_id, str(temperature), 
									str(start_freq), str(increment), str(num_increments), 
									str(num_avg), str(v_range), str(pga_gain), str(gain_factor)]) + '\n'

	file_header_3 = "freq, real, imaginary, concentration\n"

	# Open a raw data file to dump everything. This is useful in case process gets interrupted
	raw_file_name = path + '/' + session_id + '_raw.csv' 
	raw_file = open(raw_file_name, 'w+')
	raw_file.writelines([file_header_1, file_header_2, file_header_3])
	
	row_list = [0 for x in concentrations]

	# Populate the freqency list
	session_freq = list(range(start_freq, start_freq + num_increments*increment, increment))
	session_data_mag = [row_list.copy() for x in session_freq]
	session_data_phase = [row_list.copy() for x in session_freq]

	# Loop through each of the concentrations 
	for i_conc in range(n_conc):
		conc = concentrations[i_conc] #current concentration


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


		# Write the raw real and imaginary values to the raw data file
		raw_file.writelines([ str(freq[i]) + ',' + str(real[i]) + ',' + str(freq[i]) + ',' + str(conc) + '\n' for i in range(len(freq))])
		raw_file.flush()


		# Append the data to session_data arrays
		for i in range(min(len(session_freq), len(freq))):
			if (freq[i] == session_freq[i]):
				session_data_mag[i][i_conc] = impedance[i]
				session_data_phase[i][i_conc] = 0  # TODO: Update with calculated phase




		
		print ("Real range : " + str( min(real)) + " - " + str(max(real))), 	
		print ("Imaginary range : " + str( min(im)) + " - " + str(max(im))), 	
		plt.figure(1)
		plt.plot(freq, impedance, label = str(conc))
#		plt.ylim(bottom = 0)
		plt.legend()
		plt.savefig(path + '/' + session_id + '.png')
		plt.title(session_id)
		plt.pause(1)

	x = input("Press enter to save data, type x to discard ")
	if (len(x)):
		print ("Discarding data")
		exit()
# Create pandas frames and save to CSV files
	df1 = pd.DataFrame(session_data_mag)
	df1.columns = [str(x) for x in concentrations]
	df1.insert(0, 'freq', session_freq)
	mag_csv_str = df1.to_csv()
	
	mag_csv_path = path + '/' + session_id + '_mag.csv' 
	mag_csv_file = open(mag_csv_path, 'w')

	mag_csv_file.writelines([file_header_1, file_header_2, file_header_3])
	mag_csv_file.write(mag_csv_str)
	mag_csv_file.close()
	





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
