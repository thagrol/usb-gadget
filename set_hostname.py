#!/usr/bin/env python

######
## read serial number and use it to generate a hostname
##
## must be run as root
##
## run at the end of the boot sequence but before bringing up g_ether
##
## raspbian jessie or later, relies on systemd
######

## imports
import os
from getserial import getSerial
from socket import gethostname


## globals
MAX_HOSTNAME_LENGTH = 15 # windows limit, the actual RFC one is higher
HOSTNAME_PREFIX = 'PI-'

## functions
def set_host_name():
    serial  = getSerial()
    if len(serial) + len(HOSTNAME_PREFIX) > MAX_HOSTNAME_LENGTH:
        # use only the last n characters of the serial number
        # where n = MAX_HOSTNAME_LENGTH - HOSTNAME_PREFIX length
        serial = serial[-1 * (MAX_HOSTNAME_LENGTH - len(HOSTNAME_PREFIX)):]

    new_hostname = HOSTNAME_PREFIX + serial
    current_hostname = gethostname()
    if new_hostname == current_hostname:
        # hostname is correct so no need to do anything
        result = 0
    else:
        # hostnamectl set-hostname is a permanent change
        # so we only need to invoke when old and new hostnames
        # don't match
        print 'Attempting to set hostname to %s' % new_hostname
        result = os.system('hostnamectl set-hostname %s' % new_hostname)
        if result == 0:
            # successful
            # write new hostname to /boot
            os.system('hostname > /boot/hostname.txt')
            
            # may need to do some fiddling with ssh config here
            # not sure, and not sure how to either
            #
            # could restart networking here
            # currently opting to reboot instead
            os.system('reboot')
            result = -1
        else:
            print 'Unable to set new hostname'
    return result
        

## main process
if __name__ == '__main__':
    set_host_name()
