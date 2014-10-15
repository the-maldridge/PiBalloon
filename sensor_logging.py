#!/usr/bin/python

#
# Sensor polling script for PiBalloon. 
#

# I'm not a CS guy


import os
import glob
import time
from decimal import Decimal
import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT
import threading 
import Queue
import logging

# Setup the 1-wire thermal sensor
w1_base_dir = '/sys/bus/w1/devices/'
w1_device_folder = glob.glob(w1_base_dir + '28*')[0]
w1_device_file = w1_device_folder + '/w1_slave'

# Setup the BMP pressure sensor
sensor = BMP085.BMP085()

# This will read the temp by reading a file, and cutting the extra crap
def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		return temp_c

# This actually read the file for the read_temp function
def read_temp_raw():
	f = open(w1_device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

# A very simple humidity reading function
def read_humidity():
	humidity, temperature = Adafruit_DHT.read_retry(11, 17)
	return humidity

# A function to append to logfiles in the ramdisk
def write_file(value, file):
	f = open('/mnt/ramdisk/' + file, 'a')
	f.write(value + '\n')
	f.close()

# A loop to grab and write the temp data
def temp_loop():
	while True:
		output = str(round(Decimal(time.time()),2)) + ',' + str(read_temp())
		#print output
		write_file(output, 'temp.log')

# Pressure loop
def pressure_loop():
	while True:
		output = str(round(Decimal(time.time()),2)) + ',' + str(sensor.read_sealevel_pressure())
		#print output
		write_file(output, 'pressure.log')
		time.sleep(0.25)

# Humidity loop
def humidity_loop():
	while True:
		output = str(round(Decimal(time.time()),2)) + ',' + str(read_humidity())
		#print output
		write_file(output, 'humidity.log')

q = Queue.Queue()

class MasterThread:
	def __init__(self):
		self.logger=logging.getLogger("MasterThread")
		self.logger.debug("Adding Threads")

		self.threads=[]
		self.threads.append(threading.Thread(target=temp_loop))
		self.threads.append(threading.Thread(target=pressure_loop))
		self.threads.append(threading.Thread(target=humidity_loop))

	def run(self):
		self.logger.info("Enabling all threads")

		self.logger.info("Going Polythreaded")
		for thread in self.threads:
			thread.daemon = True
			thread.start()

	        #we need this thread to keep ticking
		while(True):
			if not any([thread.isAlive() for thread in self.threads]):
				break
			else:
				time.sleep(1)

		self.logger.info("All threads have terminated, exiting main thread...")



if __name__=="__main__":
	logging.basicConfig(level=logging.WARNING)
	threadCore = MasterThread()
	threadCore.run()