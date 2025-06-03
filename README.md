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

4. I2C EMULATION
  - Load kernel modules related to virtual i2c devices
  
  ```bash
    sudo modprobe virtio_pci
    sudo modprobe i2c_virtio
    sudo modprobe i2c-dev
  ```

  - Create I2C/SMBus drivers and add 3 virtual i2c chips
  
    ```bash
        sudo modprobe i2c-stub chip_addr=28,29,30 #(e.g. xx=28)
    ```
    --------------

    | Adapter | Type    | Description                         | Notes       |
    |---------|---------|-------------------------------------|-------------|
    | i2c-0   | i2c     | i915 gmbus dpa                      | I2C adapter |
    | i2c-1   | unknown | i915 gmbus dpb                      | N/A         |
    | i2c-2   | unknown | i915 gmbus dpc                      | N/A         |
    | …       | …       | …                                   | …           |
    | i2c-10  | unknown | SMBus I801 adapter at efa0          | N/A         |
    | i2c-11  | unknown | Synopsys DesignWare I2C adapter     | N/A         |
    | i2c-12  | unknown | Synopsys DesignWare I2C adapter     | N/A         |
    | i2c-13  | unknown | **SMBus stub driver**               | N/A         |

  - Check permisions for the i2c devs
    ```
    sudo chown root:$USER /dev/i2c-X
    sudo chmod g+rw /dev/i2c-X
    ```

  - Virtual host i2c devices

  ```bash
  vhost-device-i2c --socket-path=/tmp/vu_i2c- --device-list=devNum:Address #(e.g. devNum is the i2c-X device, device Address)
  ```

  

  - asd

5. SPI EMULATION
  - Load kernel modules related to virtual SPI devices
  ```
  sudo modprobe spi_virtio     
  sudo modprobe spidev
  ``` 
  


6. 