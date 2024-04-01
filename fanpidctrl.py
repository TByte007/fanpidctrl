from simple_pid import PID
from time import sleep
import subprocess
from daemonize import Daemonize
import getopt
from sys import argv

ipmitool = '/usr/local/bin/ipmitool'
pidfile = '/var/run/fanpidctrl.pid'

st = 3 # Sample time
setp = 60 # Celsius
foreground = False

# Remove 1st argument from the list
argumentList = argv[1:]
options = "hf:w:t:n"
long_options = ["help", "pid=", "wait=", "temperature="]

try:
	# Parsing argument
	arguments, values = getopt.getopt(argumentList, options, long_options)

	# checking each argument
	for opt, oval in arguments:
		if opt in ("-h", "--help"):
			print(argv[0], "[-hn] [-f pidfile] [-w wait] [-t temperature]")
		elif opt in ("-f", "--pid"):
			pidfile = oval
		elif opt in ("-w", "--wait"):
			st = int(oval)
		elif opt in ("-t", "--temperature"):
			setp = int(oval)
		elif opt in ("-n"):
			foreground = True
except getopt.error as err:
	# output error, and return with an error code
	print (str(err))



pidcpu = PID(-1, -0.2, -0.05, setpoint=setp, sample_time=st, output_limits=(1, 64)) # CPU

ctrl = lctr = 1

def get_temp():
	out = -1
	bstr = subprocess.run([ipmitool, '-c', 'sdr', 'type', 'Temperature'], stdout=subprocess.PIPE).stdout.decode()

	for line in bstr.split('\n'):
		sline = line.split(',')
		if len(sline) > 2 and sline[1].isnumeric():
			out = max(out, int(sline[1])) # get the max value
	return out

def set_fans(spd):
	global lctr

	if lctr != spd: # CPU Fan Control
		cmd = ipmitool + ' raw 0x30 0x70 0x66 0x01 0x00 ' + hex(spd)
		subprocess.run(cmd.split(), stdout=subprocess.DEVNULL)
		cmd = ipmitool + ' raw 0x30 0x70 0x66 0x01 0x01 ' + hex(spd)
		subprocess.run(cmd.split(), stdout=subprocess.DEVNULL)
	lctr = spd

# Main Loop

def main():
	global ctrl, lctr

	# Set the PWM control to full
	subprocess.run([ipmitool, 'raw', '0x30', '0x45', '0x01', '0x01'], stdout=subprocess.DEVNULL)
	sleep(3) # wait for the command to take hold

	set_fans(1) # set the fans to min

	# Get CPU fan PWM
	lctr = int(subprocess.run([ipmitool, 'raw', '0x30', '0x70', '0x66', '0x00', '0x00'], stdout=subprocess.PIPE).stdout, 16)
	# Get Periph fan PWM
	#lctr[1] = int(subprocess.run(['ipmitool', 'raw', '0x30', '0x70', '0x66', '0x00', '0x01'], stdout=subprocess.PIPE).stdout, 16)

	t = get_temp()
	while True:
    	# Compute new output from the PID according to the systems current value
#		print('Temps:', t)
		ctrl = int(pidcpu(t))

#		print('PWM:', ctrl)
		set_fans(ctrl)

		t = get_temp()
		sleep(st)

daemon = Daemonize(app="fanpidctrl", pid=pidfile, action=main, foreground=foreground)
daemon.start()
