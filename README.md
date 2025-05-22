## Emulation of an Industrial Edge Controller (IEC) network

### Version 0
Steps

1. (Cross-)Compile the kernel for raspberry Pi 0 

    ```
    git clone --depth=1 https://github.com/raspberrypi/linux.git
    cd linux
    make ARCH=arm CROSS_COMPILE=arm-none-linux-gnueabihf- bcmrpi_defconfig
    make ARCH=arm CROSS_COMPILE=arm-none-linux-gnueabihf- zImage modules dtbs -j$(nproc)
    ```

2.  
```
make ARCH=arm CROSS_COMPILE=arm-none-linux-gnueabihf- multi_v7_defconfig
make ARCH=arm CROSS_COMPILE=arm-none-linux-gnueabihf- menuconfig
# (Enable additional options like I2C/SPI if needed)
make ARCH=arm CROSS_COMPILE=arm-none-linux-gnueabihf- zImage modules dtbs -j$(nproc)

```

3.
```
GIT_SSL_NO_VERIFY=1 git clone https://github.com/…
```