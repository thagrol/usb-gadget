#!/usr/bin/env python

####
## configure unique MAC addresses and host name for pi
## report IP address and host name via usb storage gadget
##
## uses g_multi kernel module
##
## must be run as root
####

## imports
# from standard library
import os
import sys
import shutil
import time
# local files/modules
import g_ether_fixed_mac
import set_hostname
import getserial


## globals
# backing store for usb mass storagte gadget
FILESTORE_PATH = os.path.join(sys.path[0], 'fdd.img')
MOUNT_POINT = '/mnt'
# how long to wait for network (seconds)
NET_DELAY = 15


## functions


## main
if __name__ == '__main__':
    # get PI's serial number
    serial = getserial.getSerial()
    # set hostname
    if set_hostname.set_host_name() == -1:
        # hostname changed so system is rebooting
        sys.exit()

    # start usb gadget with tailored MAC addresses
    # get MAC addresses
    mac_1 = g_ether_fixed_mac.make_mac(g_ether_fixed_mac.PREFIX_1, serial)
    mac_2 = g_ether_fixed_mac.make_mac(g_ether_fixed_mac.PREFIX_2, serial)
    # load g_multi
    if os.WEXITSTATUS(os.system('modprobe g_multi host_addr=%s dev_addr=%s ro=1 removable=1' % (mac_1, mac_2))) != 0:
        sys.exit('Failed to load gadget module (g_multi)')

    # find the "file" config item in /sys
    # should be someting like
    #   /sys/devices/platform/soc/20980000.usb/gadget/lun0/file
    # not hardcoding this as the '20980000.usb' part may change across PI models and os.
    search_base = '/sys/devices/platform/soc'
    search_target = '.usb'
    search_config = 'gadget/lun0/file'
    config_file = ''
    try:
        for i in os.listdir(search_base):
            if i.endswith(search_target) and os.path.isfile(os.path.join(search_base, i, search_config)):
                # found a match
                config_file = os.path.join(search_base, i, search_config)
                break
    except OSError:
        pass
    
    # give the network some time to come up
    time.sleep(NET_DELAY)

    # write IP addresses to file on /boot
    os.system('ip addr | grep inet > /boot/ip_address.txt')

    # now need to put the data where the host can access it
    # somewhat convoluted but that's the nature of the beast
    if os.WEXITSTATUS(os.system('mount -o loop %s %s' %(FILESTORE_PATH, MOUNT_POINT))) == 0:
        # mounted FILESTORE_PATH
        try:
            shutil.copy('/boot/hostname.txt', MOUNT_POINT)
        except:
            pass
        try:
            shutil.copy('/boot/ip_address.txt', MOUNT_POINT)
        except:
            pass
        # unmount FILESTORE_PATH
        os.system('umount %s' % MOUNT_POINT)
        # pass it to the mass storage part of g_multi
        try:
            with open(config_file, 'w') as f:
                f.write('%s\n' % FILESTORE_PATH)
        except IOError:
            pass
        # and we're done
