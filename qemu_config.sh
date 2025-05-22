IEC_ROOT=$(pwd)
cd ./qemu/build

../configure \
  --target-list=arm-softmmu \
  --enable-debug \
  --enable-sdl \
  --enable-vnc \
  --enable-slirp \
  --enable-gio \
  --enable-spice \
  --enable-libusb \
  --disable-fuse\
  --enable-linux-user\
  --enable-usb-redir

