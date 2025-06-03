VM_ID="$1"

if [[ -z "$VM_ID" ]]; then
  echo "Usage: $0 <vm_id>"
  exit 1
fi

qemu-system-arm \
  -M virt \
  -cpu cortex-a7 \
  -m 256M \
  -kernel ./vms/zImage \
  -bios ./vms/u-boot.bin \
  -drive if=none,file=./vms/vm${VM_ID}_rootfs.ext2,format=raw,id=hd0 \
  -device virtio-blk-pci,drive=hd0 \
  -append "console=ttyAMA0,115200 root=/dev/vda rootfstype=ext2 rootwait rw fsck.repair=yes systemd.unit=multi-user.target" \
  -serial mon:stdio \
  -display gtk \
  -monitor unix:/tmp/qemu-monitor-socket,server,nowait \
  -object memory-backend-memfd,id=mem,size=256M,share=on \
  -numa node,memdev=mem \
  -netdev tap,id=net0,ifname=tap${VM_ID},script=no,downscript=no \
  -device virtio-net-pci,netdev=net0,mac=ee:7c:ad:d5:1d:${VM_ID}3\
  -chardev socket,id=i2c0,path=/tmp/vu_i2c${VM_ID}-0\
  -device vhost-user-i2c-pci,id=i2c0,chardev=i2c0