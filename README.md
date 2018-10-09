# usb-gadget
Various usb gadget mode stuff for raspberry pi

## aoeinit.bash
simple script to connect AoE device to g_mass_storage at bootup

usage: aoeint.sh </path/to/aoe/device>

Will load the g_mass_storage module if needed.
Must be run as root

For full instructions see
[http://www.instructables.com/id/NAS-Access-for-Non-Networked-Devices/](URL)

## refresh_shared.sh
Bash script to periodically unmount and remount the shared storage for the USB mass storage gadget. Changes made by the USB host will thus be visible to the linux device. CHanges made localy will not be propogated to the USB host.

lsof must be installed: `sudo apt install lsof`

There must be an apropriate entry in /etc/fstab for the shared storage.

Must be run as root, ideally at system startup.

Approximately once a second if the storage is mounted and there are no open files on it,
the script unmounts and remounts it.

Data corruption is still possible. This script does not address or resolve any of the issues relating to write access.

Usage: `refresh_shared.sh <mount point>`

## set_id.py
Python script to set hostname and load the g_ether USB gadget module with fix MAC address. Both derived from the Pi's serial number.

While primarily aimed at the Pi zero and zeroW, the hostname functionality can be used with any Pi. USB gadget may be usable on Pi A and A+ but this has not been tested.

Requires `dtoverlay=dwc2 `in /boot/config.txt.

Run manualy or via root's crontab, /etc/rc.local, etc.
```
usage: set_id.py [-h] [-p PREFIX] [-r] [-d] [-l LOGFILE] [-H] [-U | -M | -E] [-t]

optional arguments:
  -h, --help            show this help message and exit
  -p PREFIX, --prefix PREFIX
                        hostname prefix. Ignored if -H specified. Defaults to
                        'PI-'
  -r, --reboot          reboot if hostname changed. Ignored if -t or -H
                        specified.
  -d, --debug           Enable debug output
  -l LOGFILE, --logfile LOGFILE
                        log file. This is only useful with -d
  -H, --nohostname      Don't change hostname
  -U, --nousb           Don't start USB gadgets.
  -M, --nomsg           Don't start USB mass storage gadget.
  -E, --noether         Don't start USB ethernet gadget.
  -t, --test            Display changes but do not perform them.
```
If /boot/hostnames exists, serial number will be matched with those preesent and the corresponding hostname will be used. The new hostname will not be generated from the prefix and serial number.

Serial numbers not found in this file will cause the new hostname to be automatically generated.

## hostnames
Sample hostnames file for use with set_id.py

Lines starting with "#" are comments
Leading zeros cay be omitted from serial numbers
If a serial number appears more than once, only the first will be matched

There is no checking for duplicate hostnames. Use them at your own risk, doing so may complicate DNS lookups on your network.
```
Format:
serial_number        hostname

```
