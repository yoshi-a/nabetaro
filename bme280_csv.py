#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smbus
import time
import datetime

debug = 0
bus_number  = 1
i2c_address = 0x76

bus = smbus.SMBus(bus_number)

digT = []
digP = []
digH = []

t_fine = 0.0


def write_register(reg_address, data):
	bus.write_byte_data(i2c_address,reg_address,data)
        
def get_calib_param():
	calib = []
	
	for i in range (0x88,0x88+24):
		calib.append(bus.read_byte_data(i2c_address,i))
	calib.append(bus.read_byte_data(i2c_address,0xA1))
	for i in range (0xE1,0xE1+7):
		calib.append(bus.read_byte_data(i2c_address,i))

	digT.append((calib[1] << 8) | calib[0])
	digT.append((calib[3] << 8) | calib[2])
	digT.append((calib[5] << 8) | calib[4])
	digP.append((calib[7] << 8) | calib[6])
	digP.append((calib[9] << 8) | calib[8])
	digP.append((calib[11]<< 8) | calib[10])
	digP.append((calib[13]<< 8) | calib[12])
	digP.append((calib[15]<< 8) | calib[14])
	digP.append((calib[17]<< 8) | calib[16])
	digP.append((calib[19]<< 8) | calib[18])
	digP.append((calib[21]<< 8) | calib[20])
	digP.append((calib[23]<< 8) | calib[22])
	digH.append( calib[24] )
	digH.append((calib[26]<< 8) | calib[25])
	digH.append( calib[27] )
	digH.append((calib[28]<< 4) | (0x0F & calib[29]))
	digH.append((calib[30]<< 4) | ((calib[29] >> 4) & 0x0F))
	digH.append( calib[31] )
	
	for i in range(1,2):
		if digT[i] & 0x8000:
			digT[i] = (-digT[i] ^ 0xFFFF) + 1

	for i in range(1,8):
		if digP[i] & 0x8000:
			digP[i] = (-digP[i] ^ 0xFFFF) + 1

	for i in range(0,6):
		if digH[i] & 0x8000:
			digH[i] = (-digH[i] ^ 0xFFFF) + 1  

def probe_sensor():
	data = []
	results = {}
	for i in range (0xF7, 0xF7+8):
		data.append(bus.read_byte_data(i2c_address,i))

	results["pressure"]    = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
	results["temperature"] = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
	results["humidity"]    = (data[6] << 8)  |  data[7]

	return results

def convert_pressure(raw_p):
	global t_fine
	ret = 0

	v1 = (t_fine / 2.0) - 64000.0
	v2 = (((v1 / 4.0) * (v1 / 4.0)) / 2048) * digP[5]
	v2 = v2 + ((v1 * digP[4]) * 2.0)
	v2 = (v2 / 4.0) + (digP[3] * 65536.0)
	v1 = (((digP[2] * (((v1 / 4.0) * (v1 / 4.0)) / 8192)) / 8)  + ((digP[1] * v1) / 2.0)) / 262144
	v1 = ((32768 + v1) * digP[0]) / 32768
	
	if v1 == 0:
		return 0

	v3 = ((1048576 - raw_p) - (v2 / 4096)) * 3125
	if v3 < 0x80000000:
		v3 = (v3 * 2.0) / v1
	else:
		v3 = (v3 / v1) * 2

	v1 = (digP[8] * (((v3 / 8.0) * (v3 / 8.0)) / 8192.0)) / 4096
	v2 = ((v3 / 4.0) * digP[7]) / 8192.0
	ret = (v3 + ((v1 + v2 + digP[6]) / 16.0)) / 100

	return ret

def adjust_temperature(raw_t):
	global t_fine
	v1 = (raw_t / 16384.0 - digT[0] / 1024.0) * digT[1]
	v2 = (raw_t / 131072.0 - digT[0] / 8192.0) * (raw_t / 131072.0 - digT[0] / 8192.0) * digT[2]
	t_fine = v1 + v2
	return

def convert_temperature(raw_t):
	global t_fine
	ret = 0

	v1 = (raw_t / 16384.0 - digT[0] / 1024.0) * digT[1]
	v2 = (raw_t / 131072.0 - digT[0] / 8192.0) * (raw_t / 131072.0 - digT[0] / 8192.0) * digT[2]
	ret = (v1 + v2) / 5120.0

	return ret

def convert_humidity(raw_h):
	global t_fine
	ret = 0

	v1 = t_fine - 76800.0
	if v1 == 0:
		return 0

	v2 = (raw_h - (digH[3] * 64.0 + digH[4]/16384.0 * v1)) * (digH[1] / 65536.0 * (1.0 + digH[5] / 67108864.0 * v1 * (1.0 + digH[2] / 67108864.0 * v1)))

	ret = v2 * (1.0 - digH[0] * v2 / 524288.0)
	
	if ret > 100.0:
		ret = 100.0
	elif ret < 0.0:
		ret = 0.0

	return ret

def init_bme280():
	os_flag_pres = 1
	os_flag_temp = 1
	os_flag_hum  = 1
	mode = 3
	standby_time = 5
	filter = 0
	enable_3wire_spi = 0

	ctrl_meas_reg = (os_flag_temp << 5) | (os_flag_pres << 2) | mode
	config_reg    = (standby_time << 5) | (filter << 2) | enable_3wire_spi
	ctrl_hum_reg  = os_flag_hum

	write_register(0xF2,ctrl_hum_reg)
	write_register(0xF4,ctrl_meas_reg)
	write_register(0xF5,config_reg)

def main():
	try:
		init_bme280()
		get_calib_param()

		raw = probe_sensor()

		if debug == 1:
			for k, v in raw.items():
				print(k, v)

		adjust_temperature(raw["temperature"])
		t = convert_temperature(raw["temperature"])
		h = convert_humidity(raw["humidity"])
		p = convert_pressure(raw["pressure"])

		if debug == 1:
			print "temp : %-5.2f ℃" % (t)
			print "pres : %7.2f hPa" % (p)
			print "hum : %6.2f %%" % (h)

		now = datetime.datetime.now()
		d = now.strftime(u"%Y/%m/%d %H:%M:%S")

		print "%s,%-.2f,%.2f,%.2f" % (d, t, h, p)

	except KeyboardInterrupt:
		pass

if __name__ == '__main__':
	main()
