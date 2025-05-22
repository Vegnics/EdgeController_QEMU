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
  -netdev user,id=net0,hostfwd=tcp::5022-:22 \
  -device virtio-net-pci,netdev=net0\
  -chardev socket,id=i2c0,path=/tmp/vu_i2c-0\
  -device vhost-user-i2c-pci,id=i2c0,chardev=i2c0\
  -d guest_errors

  #-d unimp\
  #
  #  -device generic-spi\
  # -dtb ./buildroot/output/images/virt_arm32.dtb\
  #   -s 19,virtio-i2c,4:1C\
  # #\
  #  -dtb ./buildroot/output/images/virt_arm32_patched.dtb\
  #   -m 256M \
  
  


#-device smsc95xx,netdev=net0,mac=52:54:00:12:34:56

#  -netdev user,id=net0,hostfwd=tcp::5022-:22 \
#  -device smsc95xx,netdev=net0,mac=52:54:00:12:34:56
 #\
 # -serial stdio \
 # -display none \
# systemd.unit=multi-user.target"\
#  -icount shift=1\
#  -append "console=ttyAMA0,115200 root=/dev/mmcblk0p2 rootfstype=ext4 rootwait rw systemd.unit=multi-user.target" \
#\
#  -netdev user,id=net0,hostfwd=tcp::5022-:22 \
#  -device usb-net,netdev=net0\
#  -display vnc=:1
   