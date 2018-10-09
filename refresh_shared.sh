#!/bin/bash

# simple script to update linux view of storage exported via
# the usb mass storage gadget
#
# This is a kluge so there is still the possibility for
# bad data and file corruption especially if mounted read/write
#
# must be run as root
#
# an aproprite entry for the exported storage must exist in /etc/fstab
# lsof must be installed (sudo apt install lsof)

echo $1

if [ $# != 1 ]; then
	echo "usage: $0 <mount point>" > /dev/stderr
	exit 1
fi

while :
do
    mountpoint $1 > /dev/null
    if [ $? = 0 ]; then
        if [ `lsof $1 | wc -l` = 0 ]; then
            # no open files so this should be safe
            umount $1
            mount $1
        fi
    fi
    sleep 1
done
