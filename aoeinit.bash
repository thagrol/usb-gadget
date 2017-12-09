#!/bin/bash

# simple script to connect AoE device to g_mass_storage
# at bootup
#
# usage:
#	aoeint.sh </path/to/aoe/device>
#
# script will load the g_mass_storage module if needed
# must be run as root
#
# for full instructions see
#   http://www.instructables.com/id/NAS-Access-for-Non-Networked-Devices/

if [ $# != 1 ]; then
	echo "usage: aoeint.sh </path/to/aoe/device>" > /dev/stderr
	exit 1
fi

# detect AoE devices
/sbin/aoe-discover
if [ $? != 0 ]; then
	echo "Could not detect AoE devices. has the aoe module been loaded?" > /dev/stderr
	exit 1
fi
/bin/sleep 5 # give the AoE daemons some time to work...

# check AoE device is a valid block device
if [ ! -b "$1" ]; then
	echo "$1 is not a block device." > /dev/stderr
	exit 1
fi

# try to load g_mass_storage
if [ "$0" == "aoeinit-rw.bash" ]; then
	/sbin/modprobe --first-time g_mass_storage removable=y file="$1"
else
	/sbin/modprobe --first-time g_mass_storage removable=y ro=1 file="$1"
fi

if [ $? != 0 ]; then
	echo "Failed to load g_mass_storage." >/dev/stderr
	exit 1
else
	exit 0
fi