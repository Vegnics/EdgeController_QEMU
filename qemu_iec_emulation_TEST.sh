#!/bin/bash
#./qemu/build/qemu-system-arm \
qemu-system-arm \
  -M virt\
  -cpu cortex-a7\
  -m 256M\
  -kernel ./buildroot/output/images/zImage \
  -bios ./buildroot/output/images/u-boot.bin\
  -drive if=none,file=./buildroot/output/images/rootfs.ext2,format=raw,id=hd0 \
  -device virtio-blk-pci,drive=hd0 \
  -append "console=ttyAMA0,115200 root=/dev/vda rootfstype=ext2 rootwait rw fsck.repair=yes systemd.unit=multi-user.target" \
  -serial mon:stdio \
  -display gtk \
  -monitor unix:/tmp/qemu-monitor-socket,server,nowait\
  -object memory-backend-memfd,id=mem,size=256M,share=on \
  -numa node,memdev=mem \
  -netdev tap,id=net0,ifname=tap0,script=no,downscript=no \
  -device virtio-net-pci,netdev=net0 \
  -chardev socket,id=i2c0,path=/tmp/vu_i2c-0\
  -device vhost-user-i2c-pci,id=i2c0,chardev=i2c0\
  -d guest_errors

#### NAT mode
#   -netdev user,id=net0,hostfwd=tcp::5022-:22 \
#  -device virtio-net-pci,netdev=net0\
#  -display vnc=:1
#  -netdev tap,id=net0,ifname=tap0,script=no,downscript=no \
   