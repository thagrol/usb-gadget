#!/usr/bin/env python

"""
python script to set host name and USB ethernet gadget MAC address
from Pi's serial number

Aimed at Pi Zero, ZeroW, ZeroWH, A, A+ and any other models capable
of running as a USB gadget.
USB Host will see ethernet and mass storage gadgets.

Add 'dtoverlay=dwc2' to /boot/config.txt
For A and A+ add 'dtoverlay=dwc2,dr_mode=peripheral' instead
Remove any references to g_* modules from
    /boot/cmdline.txt
    /etc/modules
    etc

libcomposite/USB gadget code based on that present on https://github.com/ckuethe/usbarmory/wiki/USB-Gadgets
"""

## Imports
import argparse
import logging
import os
import subprocess
import sys
import warnings
from socket import gethostname


## Globals
# logging
LOG_LEVEL = 30 # warnings
LOG_LEVEL = logging.DEBUG # uncomment for debug output
# USB gadget config
USB_BASE_DIR = '/sys/kernel/config/usb_gadget'
USB_DEV_NAME = 'foo'
HOSTNAME_PREFIX = 'PI-'
MAC_PREFIX_HOST = '02'
MAC_PREFIX_DEVICE = '06'
# hostname
MAX_HOSTNAME_LENGTH = 15 # windows limit, the actual RFC one is higher
# config output file
ID_FILE = 'id.txt'
IP_FILE = 'ip_address.txt'
ID_PATH = '/boot'


## USB gadget
def makeStorage(path=None):
    filename = os.tempnam(path)
    subprocess.check_call(['/sbin/mkfs.msdos', '-C', filename, '1440'])
    return filename

def USBConfig(name=USB_DEV_NAME,
              host_mac='02:27:eb:b3:96:23',
              dev_mac='06:27:eb:b3:96:23',
              storage='',
              devserial='1234567890'):

    # directory names/paths
    device_base = os.path.join(USB_BASE_DIR, USB_DEV_NAME)
    strings_dir = os.path.join(device_base, 'strings/0x409')
    functions_dir = os.path.join(device_base, 'functions')
    ecm_dir = os.path.join(functions_dir, 'ecm.usb0')
    mass_dir = os.path.join(functions_dir, 'mass_storage.usb0')
    lun_dir = os.path.join(mass_dir, 'lun.0')
    configs_dir = os.path.join(device_base, 'configs/c.1')
    configstrings_dir = os.path.join(device_base, 'configs/c.1/strings/0x409')

    # create device directories
    logging.debug('\t\tCreating directories')
    logging.debug('\t\t\t%s' % device_base)
    os.makedirs(device_base)
    logging.debug('\t\t\t%s' % strings_dir)
    os.makedirs(strings_dir)
    logging.debug('\t\t\t%s' % ecm_dir)
    os.makedirs(ecm_dir)
    logging.debug('\t\t\t%s' % mass_dir)
    os.makedirs(mass_dir)
    logging.debug('\t\t\t%s' % configstrings_dir)
    os.makedirs(configstrings_dir)

    # device data
    with open(os.path.join(device_base, 'idVendor'),'w+') as f:
        f.write('0x1d6b')
    with open(os.path.join(device_base, 'idProduct'),'w+') as f:
        f.write('0x0104')
    with open(os.path.join(device_base, 'bcdDevice'),'w+') as f:
        f.write('0x0100')
    with open(os.path.join(device_base, 'bcdUSB'),'w+') as f:
        f.write('0x0200')

    # strings
    with open(os.path.join(strings_dir, 'serialnumber'),'w+') as f:
        f.write(devserial)
    with open(os.path.join(strings_dir, 'manufacturer'),'w+') as f:
        f.write('thagrol thagrolson')
    with open(os.path.join(strings_dir, 'product'),'w+') as f:
        f.write(name)

    # MAC addresses
    with open(os.path.join(ecm_dir, 'host_addr'),'w+') as f:
        f.write(host_mac)
    with open(os.path.join(ecm_dir, 'dev_addr'),'w+') as f:
        f.write(dev_mac)

    # mass storage
    with open(os.path.join(mass_dir, 'stall'), 'w+') as f:
        f.write('1')
    with open(os.path.join(lun_dir, 'removable'), 'w+') as f:
        f.write('1')
    with open(os.path.join(lun_dir, 'ro'), 'w+') as f:
        f.write('1')
    with open(os.path.join(lun_dir, 'nofua'), 'w+') as f:
        f.write('0')
    with open(os.path.join(lun_dir, 'file'), 'w+') as f:
        f.write(storage)

    # configs
    with open(os.path.join(configstrings_dir, 'configuration'),'w+') as f:
        f.write('Config 1: ECM network')
    with open(os.path.join(configs_dir, 'MaxPower'), 'w+') as f:
        f.write('250')
    os.symlink(os.path.join(functions_dir, 'ecm.usb0'),
               os.path.join(configs_dir, 'ecm.usb0'))
    os.symlink(os.path.join(functions_dir, 'mass_storage.usb0'),
               os.path.join(configs_dir, 'mass_storage.usb0'))
    os.system('ls /sys/class/udc > %s' % os.path.join(device_base, 'UDC'))

def USBSetStorage(storage):
    target = os.path.join(USB_BASE_DIR, USB_DEV_NAME, 'functions', 'mass_storage.usb0', 'lun.0', 'file')
    with open(target, 'w+') as f:
        f.write(storage)    


## Functions - hostname
def validHostname(name):
    """Validate hostname"""
    validchars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-'
    minlength = 1
    maxlength = 15

    # check length
    if len(name) < minlength or len(name) > maxlength:
        logging.debug('New hostname "%s" has invalid length (%s)' % (name, len(name)))
        return 1

    # must not start with '-' or a number
    if name.startswith('-') or name[0].isdigit():
        logging.debug('New hostname "%s" cannot start with "-" or a number' % name)
        return 2

    # check for invalid characters
    for c in name:
        if c in validchars:
            pass
        else:
            logging.debug('New hostname "%s" contains invlaid character(s).' % name)
            return 3
    # all tests passed so
    return 0

def validPrefix(prefix):
    """Validate hostname prefix"""
    return validHostname(prefix)

def hostnamePrefix(prefix):
    """type handler for agrparse"""
    v = validPrefix(prefix)
    if v == 0:
        return prefix
    elif v ==1:
        raise argparse.ArgumentTypeError("'%s' has invalid length (0 < length < 16)" % prefix)
    elif v== 2:
        raise argparse.ArgumentTypeError("'%s' cannot start with '-' or a number." % prefix)
    elif v == 3:
        raise argparse.ArgumentTypeError("'%s' contains invalid characters." % prefix)
    else:
        raise argparse.ArgumentTypeError("'%s' is invalid." % prefix)

def newHostname(prefix = HOSTNAME_PREFIX, serial = None):
    """
    Calculate new hostname from serial number and prefix
    """

    if serial is None:
        serial = getSerial()
    if len(serial) + len(HOSTNAME_PREFIX) > MAX_HOSTNAME_LENGTH:
        # use only the last n characters of the serial number
        # where n = MAX_HOSTNAME_LENGTH - HOSTNAME_PREFIX length
        serial = serial[-1 * (MAX_HOSTNAME_LENGTH - len(HOSTNAME_PREFIX)):]

    return prefix + serial

def hostnamesMatch(new, old):
    """
    Compare hostnames ignoring case
    """

    return new.lower() == old.lower()

def setHostname(newname, oldname, reboot=True):
    """
    Set new hostname
    """

    logging.debug('\tAttempting to set new hostname')
    cmd = ['hostnamectl', '--no-ask-password', 'set-hostname', newname]
    logging.debug('\t\tCalling subprocess: %s' % cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logging.error('\t\tFailed to change hostname. Call to hostnamectl returned "%s"' % e.output.strip())
        if args.logfile:
            sys.stderr.write('Failed to change hostname. Call to hostnamectl returned "%s"\n' % e.output.strip())
        return False
    else:
        logging.debug('\t\tSucceeded.')
    # update /etc/hosts as it may have a reference to the old hostname
    logging.debug('\t\tBacking up old /etc/hosts file to /etc/hosts.bak')
    try:
        os.rename('/etc/hosts', '/etc/hosts.bak')
    except OSError as e:
        logging.warning('\t\tFailed to backup /etc/hosts (%s) it will not be modified.' % e)
    else:
        logging.debug('\t\t/etc/hosts: Replacing old hostname with new one.')
        with open('/etc/hosts.bak', 'r') as hb:
            oh = hb.read()
        with open('/etc/hosts', 'w') as nh:
            for l in oh.splitlines(True):
                if l.startswith('127.'):
                    l = l.replace(oldname, newname)
                nh.write(l)

    if reboot:
        logging.debug('\tRebooting')
        subprocess.call('reboot')

    return True


## Functions - Misc
def iAmNotRoot():
    """Check if running as root."""
##    logging.debug('Checking UID')
    return not(os.geteuid() == 0)

def getSerial():
    """get serial number"""
    logging.info('Reading serial number')
    # try device tree first
    if os.path.isfile('/proc/device-tree/serial-number'):
        logging.debug('\tfrom /proc/device-tree/serial-number')
        with open('/proc/device-tree/serial-number') as f:
            cpuserial = f.read()
        # strip atrailing \x00
        cpuserial = cpuserial.strip('\x00')
    else:
        logging.debug('\tfrom /proc/cpuinfo')
        # Extract serial from /proc/cpuinfo file
        # from https://www.raspberrypi-spy.co.uk/2012/09/getting-your-raspberry-pi-serial-number-using-python/    
        cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
              if line[0:6]=='Serial':
                cpuserial = line[10:26]
            f.close()
        except:
            cpuserial = "ERROR000000000"
    logging.debug('\tgot %s' % cpuserial)
    return cpuserial

def make_mac(prefix, serial):
    """
    make formatted MAC address from prefix and serial
    prefix and serial are expected to be strings
    prefix must be 2 characters and both must be hex digits
    """
      
    # get last 12 digits of serial
    short_serial = serial[-12:]
    # add prefix
    raw_mac = prefix + short_serial[len(prefix):]
    # format mac
    mac = ''
    for i in range(0, len(raw_mac), 2):
        mac += raw_mac[i:i + 2] + ':'
    # strip trailing ':'
    mac = mac[:-1]

    return mac

def write_config(hostname, devmac=None, hostmac=None,
                 serial=None,
                 target=os.path.join(ID_PATH,ID_FILE)):
    if serial is None:
        serial = getSerial()
    with open(target, 'w+') as f:
        f.write('hostname:\t%s\r\n' % hostname)
        f.write('serial:\t\t%s\r\n' % serial)
        f.write('my MAC:\t\t%s\r\n' % devmac)
        f.write('host MAC:\t%s<\r\n' % hostmac)
    

## Main
if iAmNotRoot():
##    logging.debug('Not root')
    sys.exit('Must be root')

# parse cmdline
parser= argparse.ArgumentParser(description='Configure hostname and USB gadget MAC addresses from serial number')
parser.add_argument('-p','--prefix',
                    action='store',
                    dest='prefix',
                    default=HOSTNAME_PREFIX, nargs=1,
                    type=hostnamePrefix,
                    help="hostname prefix. Ignored if -H specified. Defaults to '%(default)s'")
parser.add_argument('-t', '--test',
                    action='store_true',
                    dest='test',
                    help="test mode. Display changes but don't apply them")
parser.add_argument('-r', '--reboot',
                    action='store_true',
                    dest='reboot',
                    help="reboot if hostname changed. Ignored if -t or -H specified.")
parser.add_argument('-l', '--logfile',
                    action='store',
                    default=None, #'/tmp/%(prog)s.log',
##                    nargs=1,
                    help="log file. This is only useful with -d")
parser.add_argument('-d', '--debug',
                        action='store_const',
                        dest='debug',
                        const=logging.DEBUG,
                        default=logging.WARNING,
                        help='Enable debug output')
funcgroup = parser.add_mutually_exclusive_group()
funcgroup.add_argument('-U', '--nousb',
                       action='store_false',
                       dest='usb',
                       help="Don't start USB gadgets.")
funcgroup.add_argument('-H', '--nohostname',
                       action='store_false',
                       dest='hostname',
                       help="Don't change hostname")
args = parser.parse_args()

# have args can now do something
# logging
loggerconfig = {'format':'%(levelname)s\t: %(message)s',
                'level':args.debug}
if args.logfile:
    loggerconfig['filename'] = args.logfile

logging.basicConfig(**loggerconfig)
logging.debug('Command line args: %s' % args)

try:
    # disable warnings
    if not sys.warnoptions:
        warnings.simplefilter('ignore')
    # serial number
    serial = getSerial()
    # MAC addresses
    logging.debug('Creating MAC addresses')
    hostmac = None
    devicemac = None
    if args.usb:
        hostmac = make_mac(MAC_PREFIX_HOST, serial)
        devicemac = make_mac(MAC_PREFIX_DEVICE, serial)
    logging.debug('\tHost\t%s' % hostmac)
    logging.debug('\tDevice\t%s' % devicemac)
    # hostname
    if args.hostname:
        logging.info('Starting hostname change process')
        current_hostname = gethostname()
        logging.debug('\tCurrent hostname\t%s' % current_hostname)
        new_hostname = newHostname(HOSTNAME_PREFIX, serial)
        logging.debug('\tNew hostname\t\t%s' % new_hostname)
        if hostnamesMatch(current_hostname, new_hostname):
            logging.debug('\t hostanmes match. No action required')
            if args.test:
                print('Hostname already set to correct value. No action required')
        else:
            logging.debug("\thostanmes don't match.")
            if args.test:
                print('Hostname will be changed from "%s" to "%s"' % (current_hostname, new_hostname))
                print('/etc/hosts will be ammended to match')
                print('new hostname will be writen to /boot/hostname.txt')
            else:
                logging.debug('\tChanging hostname')
                setHostname(new_hostname,current_hostname, reboot=args.reboot)
    write_config(hostname=gethostname(),
                 devmac=devicemac,
                 hostmac=hostmac)
    # start USB gadgets
    if args.usb:
        logging.info('Starting USB gadget(s)')
        if args.test:
            print('USB ethernet gadget will be started with host MAC: %s, device MAC: %s' % (hostmac, devicemac))
        else:
            logging.debug('\tLoading libcomposite')
            try:
                subprocess.check_output(['modprobe', 'libcomposite'], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                logging.error('\tFailed: "%s" Aborting USB gadget config' % e.output.strip())
                if args.logfile:
                    sys.stderr.write('\tFailed to load libcomposite: "%s" Aborting USB gadget config' % e.output.strip())
            else:
                USBConfig(name=USB_DEV_NAME,
                          host_mac=hostmac,
                          dev_mac=devicemac,
                          storage='',
                          devserial=serial)
                # backing store
                logging.debug('Creating mass_storage backingstore')
                # create it
                storage = makeStorage()
                logging.debug('\t%s' % storage)
                # mount it
                logging.debug('\tCreating mount point')
                mount_point = os.tempnam()
                os.mkdir(mount_point)
                logging.debug('\tmounting')
                subprocess.check_call(['mount', storage, mount_point])
                # copy files
                logging.debug('\tcopying files')
                logging.debug('\t\t%s' % os.path.join(ID_PATH, ID_FILE))
                subprocess.call(['cp', os.path.join(ID_PATH, ID_FILE), os.path.join(mount_point, ID_FILE)])
                # unmount it
                logging.debug('\tunmounting')
                subprocess.check_call(['umount', mount_point])
                # delete mount point
                logging.debug('\tdeleting mount point')
                os.rmdir(mount_point)
                # export it
                logging.debug('\texporting')
                USBSetStorage(storage)

except KeyboardInterrupt:
    raise
except:
    if args.logfile:
        logging.exception('Uncaught exception: ')
    raise
finally:
    logging.shutdown()
