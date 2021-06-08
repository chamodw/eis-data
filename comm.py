#!/usr/bin/env python3
import serial
import numpy as np
import sys
import struct
import matplotlib.pyplot as plt
from datetime import datetime



gain_factor = 2.2177474841604154e-09


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
	start_freq=10000
	increment = 500
	num_increments=160
	num_avg = 2
	v_range = 1
	pga_gain = 1


#User parameters
	session_id = 'avg2'
	temperature = 25
	concentrations = [1, 2]


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

	file_header_1 = "#, session_id, temperature, start_freq, increment, num_increments, num_avg, v_range, pga_gain, gain_factor\n"	
	file_header = '#' + ','.join([session_id, str(temperature), 
									str(start_freq), str(increment), str(num_increments), 
									str(num_avg), str(v_range), str(pga_gain), str(gain_factor)]) + '\n'

	file_header_3 = "freq, real, imaginary, concentration\n"

	# Open a raw data file to dump everything. This is useful in case process gets interrupted
	raw_file_name = path + '/' + session_id + '.csv' 
	raw_file = open(raw_file_name, 'w+')

	raw_file.writelines([file_header_1, file_header, file_header_3])


	for i_conc in range(n_conc):
		conc = concentrations[i_conc] #current concentration


		#Print the progress 
		print(getProgressBar(i_conc+1, n_conc))

		# Announce the next concentration in the line up
		printColor ('*** ' + str(conc) + ' ***', 'g')	
		x = input("Press enter collect data")

		print("Starting data collection..." )






#	#Open file for data recording
#	now=datetime.now()
		#out_file=open(path + '/' + session_id + '_' + str(concentrations[i_conc]) +  '.txt', 'w');
#
#	#record the parameters
#	header_line = ",,," + session_id + ',' + str(conc) 
#	out_file.write(header_line)
#	out_file.write("\n")
			
		# Command the hardware to perform a sweep and retrieve the data
		(freq, real, im) = performSweep(ser, start_freq = start_freq, increment_freq = increment, 
								num_increments = num_increments, num_avg = num_avg, 
									v_range = v_range, pga_gain = pga_gain)
		impedance = impedancePhase(real, im)


		# Write the raw real and imaginary values to the raw data file
		raw_file.writelines([ str(freq[i]) + ',' + str(real[i]) + ',' + str(freq[i]) + ',' + str(conc) + '\n' for i in range(len(freq))])

		raw_file.flush()
		
		print ("Real range : " + str( min(real)) + " - " + str(max(real))), 	
		print ("Imaginary range : " + str( min(im)) + " - " + str(max(im))), 	
		plt.figure(1)
		plt.plot(freq, impedance, label = 'Mag')
		plt.legend(str(concentrations[i_conc]))
		plt.pause(1)



	#	out_file.close()
	#	printColor("\nData writeen to " + out_file.name, 'g')







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
	p = '='*int(i*80/n) + '-'*(80-int(i*80/n)) + '|'
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
