#!/bin/bash -exu
sudo fdisk /dev/sdc <<EOF
t
83
w
EOF

sudo mkfs.ext4 /dev/sdc1
sudo tune2fs -m 0 /dev/sdc1
sudo eject /dev/sdc
