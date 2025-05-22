#include "qemu/osdep.h"
#include "hw/sysbus.h"
#include "hw/ssi/ssi.h"
#include "hw/irq.h"
#include "qapi/error.h"
#include "qemu/log.h"

#define TYPE_GENERIC_SPI "generic-spi"
OBJECT_DECLARE_SIMPLE_TYPE(GenericSPIState, GENERIC_SPI)

struct GenericSPIState {
    SysBusDevice parent_obj;
    SSIBus *spi_bus;
    MemoryRegion iomem;
};

static uint64_t generic_spi_read(void *opaque, hwaddr addr, unsigned size)
{
    qemu_log_mask(LOG_GUEST_ERROR, "[generic-spi] Read @0x%" HWADDR_PRIx " (%d bytes)\n", addr, size);
    return 0xFF;
}

static void generic_spi_write(void *opaque, hwaddr addr, uint64_t val, unsigned size)
{
    qemu_log_mask(LOG_GUEST_ERROR, "[generic-spi] Write @0x%" HWADDR_PRIx " = 0x%" PRIx64 " (%d bytes)\n", addr, val, size);
}

static const MemoryRegionOps generic_spi_ops = {
    .read = generic_spi_read,
    .write = generic_spi_write,
    .endianness = DEVICE_NATIVE_ENDIAN,
    .valid.min_access_size = 1,
    .valid.max_access_size = 4,
    .impl.min_access_size = 1,
    .impl.max_access_size = 4,
};

static void generic_spi_realize(DeviceState *dev, Error **errp)
{
    GenericSPIState *s = GENERIC_SPI(dev);
    s->spi_bus = ssi_create_bus(dev, "generic-spi");
    memory_region_init_io(&s->iomem, OBJECT(dev), &generic_spi_ops, s, "generic-spi", 0x100);
    sysbus_init_mmio(SYS_BUS_DEVICE(dev), &s->iomem);
}

static void generic_spi_class_init(ObjectClass *klass, const void *data) 
{
    DeviceClass *dc = DEVICE_CLASS(klass);
    dc->realize = generic_spi_realize;
    dc->desc = "Dummy Generic SPI Controller";
}

static const TypeInfo generic_spi_info = {
    .name          = "generic-spi",
    .parent        = TYPE_SYS_BUS_DEVICE,
    .instance_size = sizeof(GenericSPIState),
    .class_init    = generic_spi_class_init,
};

static void generic_spi_register_types(void)
{
    type_register_static(&generic_spi_info);
}

type_init(generic_spi_register_types);
