#!/bin/bash -eu
mount /dev/sdc1 /media/cmip5
ls /media/cmip5/
ls /media/cmip5/decadal*
find /media/cmip5 -type d -exec chmod o+rx {} +;
find /media/cmip5 -type f -exec chmod o+r {} +;
umount /dev/sdc1
eject /dev/sdc
