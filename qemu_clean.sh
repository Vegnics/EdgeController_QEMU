IEC_ROOT=$(pwd)
cd ./qemu/build
make distclean
cd $IEC_ROOT
rm -rf ./qemu/build
mkdir ./qemu/build
echo QEMU built cleaned!!