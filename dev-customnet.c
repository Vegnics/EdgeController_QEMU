// hw/usb/dev-customnet.c
#include "qemu/osdep.h"
#include "hw/usb.h"
#include "hw/usb/desc.h"
#include "qemu/module.h"

typedef struct {
    USBDevice dev;
    USBDesc desc;
} USBCustomNetState;

static void usb_customnet_realize(USBDevice *dev, Error **errp) {
    usb_desc_init(dev);
    fprintf(stderr, "usb-customnet: device initialized.\n");
}

static const USBDescDevice desc_device = {
    .bLength            = sizeof(USBDescDevice),
    .bDescriptorType    = USB_DT_DEVICE,
    .bcdUSB             = 0x0110,
    .bDeviceClass       = USB_CLASS_COMM,
    .bDeviceSubClass    = 0,
    .bDeviceProtocol    = 0,
    .bMaxPacketSize0    = 8,
    .idVendor           = 0x1d6b,
    .idProduct          = 0x0101,
    .bcdDevice          = 0x0100,
    .iManufacturer      = 1,
    .iProduct           = 2,
    .iSerialNumber      = 3,
    .bNumConfigurations = 1,
};

static void usb_customnet_class_init(ObjectClass *klass, void *data) {
    USBDeviceClass *k = USB_DEVICE_CLASS(klass);
    k->realize = usb_customnet_realize;
    k->product_desc = "Custom USB Network Device";
    k->usb_desc = &desc_device;
}

static const TypeInfo usb_customnet_info = {
    .name          = "usb-customnet",
    .parent        = TYPE_USB_DEVICE,
    .instance_size = sizeof(USBCustomNetState),
    .class_init    = usb_customnet_class_init,
};

static void usb_customnet_register_types(void) {
    type_register_static(&usb_customnet_info);
}

type_init(usb_customnet_register_types)