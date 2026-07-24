# SmartUSBHub Documentation

[简体中文](./README_cn.md)

This directory contains user guides, technical specifications, and shared documentation for the SmartUSBHub product family.

## Product Features

SmartUSBHub is a family of programmable USB hubs with per-channel power control. Data-line control and voltage/current sensing are available on supported models. The product family is designed for development, automated testing, and device management.

## Product Guides

| Product Name | Model / Order Code | Channels | USB Standard | User Guide | Technical Specification |
| --- | --- | ---: | --- | --- | --- |
| SmartUSBHub Pro 4CH USB2.0 | `HBP_USB2_4CH`, `HBP_USB2_4CH_PSU` | 4 | USB 2.0 High-Speed | [User Guide](./products/usb2_4p/user_guide.md) | [Technical Specification](./products/usb2_4p/datasheet.md) |
| SmartUSBHub Pro 7CH USB2.0 | `HBP_USB2_7CH`, `HBP_USB2_7CH_ADV` | 7 | USB 2.0 High-Speed | [User Guide](./products/usb2_7p/user_guide.md) | [Technical Specification](./products/usb2_7p/datasheet.md) |

## Capability Matrix

| Product | Independent Power Control | USB2 Data-Line Control | Voltage/Current Sensing | BC 1.2 CDP | Local Channel Buttons |
| --- | --- | --- | --- | --- | --- |
| SmartUSBHub Pro 4CH USB2.0 | Yes | Yes | Yes | Yes, up to 1.5 A | Yes |
| SmartUSBHub Pro 7CH USB2.0 | Yes | Yes | ADV version only | Yes | No |

## Developer Documentation

- Quick start: [../README.md#quick-start](../README.md#quick-start)
- Communication protocol: [SmartUSBHub protocol](./protocol.md)
- Python library overview: [../README.md](../README.md)
- Python examples: [../examples/README.md](../examples/README.md)

Use `hub.get_channels()` in software to get the actual channel list of the connected product. Examples should not assume that every SmartUSBHub device has four channels.
