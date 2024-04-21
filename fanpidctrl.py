from simple_pid import PID
from time import sleep
import subprocess
from daemonize import Daemonize
import os, getopt, select
from sys import argv

ipmitool = '/usr/local/bin/ipmitool'
pidfile = '/var/run/fanpidctrl.pid'

st = 3 # Sample time
setp = 60 # Celsius
foreground = False
min_pwm = 1

# Remove 1st argument from the list
argumentList = argv[1:]
options = "hf:w:t:m:n"
long_options = ["help", "pid=", "wait=", "temperature=", "min="]

try:
	# Parsing argument
	arguments, values = getopt.getopt(argumentList, options, long_options)

	# checking each argument
	for opt, oval in arguments:
		if opt in ("-h", "--help"):
			print(argv[0], "[-hn] [-f pidfile] [-w wait] [-t temperature] [-m min_pwm]")
		elif opt in ("-f", "--pid"):
			pidfile = oval
		elif opt in ("-w", "--wait"):
			st = int(oval)
		elif opt in ("-t", "--temperature"):
			setp = int(oval)
		elif opt in ("-m", "--min"):
			min_pwm = int(oval)
		elif opt in ("-n"):
			foreground = True
except getopt.error as err:
	# output error, and return with an error code
	print (str(err))

pidcpu = PID(-1, -0.2, -0.05, setpoint=setp, sample_time=st, output_limits=(min_pwm, 64)) # CPU
ctrl = lctr = 1

def ipmi_send_cmd(cmd):
	global po, p

	p.stdin.write(cmd + '\n')
	p.stdin.flush()
	os.set_blocking(p.stdout.fileno(), True)
	p.stdout.readline()
	os.set_blocking(p.stdout.fileno(), False)
	out = ''
	while(po.poll(100)):
		out += p.stdout.read(1000)
	lp = out.rfind('\n') # last \n pos
	if lp == -1:
		return out
	return out[:lp]

def get_temp():
	out = -1
	bstr = ipmi_send_cmd('sdr type Temperature')
	for line in bstr.split('\n'):
		sline = line.split(',')
		if len(sline) > 2 and sline[1].isnumeric():
			out = max(out, int(sline[1])) # get the max value
	return out

def set_fans(spd):
	global lctr

	if lctr != spd: # CPU Fan Control
		ipmi_send_cmd('raw 0x30 0x70 0x66 0x01 0x00 ' + hex(spd))
		ipmi_send_cmd('raw 0x30 0x70 0x66 0x01 0x01 ' + hex(spd))
	lctr = spd

# Main Loop

def main():
	global ctrl, lctr, po, p

	p = subprocess.Popen([ipmitool, 'shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

	# Create a poll object
	po = select.poll()
	po.register(p.stdout, select.POLLIN)

	# Set ipmitool to csv output
	ipmi_send_cmd('set csv')

	# Check if the fans are set to Full
	pwmc = int(ipmi_send_cmd('raw 0x30 0x45 0x00'))
	if pwmc != 1:
		# Set the PWM control to Full
		# so the IPMI would not mess up with the management
		# (it would be loud for few seconds after reboot)
		ipmi_send_cmd('raw 0x30 0x45 0x01 0x01')
		sleep(3) # wait for the command to take hold

	set_fans(min_pwm) # set the fans to min

	# Get CPU fan PWM
	lctr = int(ipmi_send_cmd('raw 0x30 0x70 0x66 0x00 0x00'))
	# Get Periph fan PWM
	#ipmi_send_cmd('raw 0x30 0x70 0x66 0x00 0x01')

	t = get_temp()
	while True:
#		print('Temps:', t)
		ctrl = int(pidcpu(t))

#		print('PWM:', ctrl)
		set_fans(ctrl)

		# just to be sure we got an actual temperature
		nt = get_temp()
		if nt != -1:
			t = nt
		sleep(st)

daemon = Daemonize(app="fanpidctrl", pid=pidfile, action=main, foreground=foreground)
daemon.start()
