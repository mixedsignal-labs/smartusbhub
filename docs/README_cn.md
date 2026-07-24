# SmartUSBHub 文档

[English](./README.md)

此目录用于存放 SmartUSBHub 产品系列的用户文档。不同产品的端口数量、供电能力、测量能力和专用功能可能不同，请先选择产品型号，再进入对应文档。

## 产品特性

SmartUSBHub 是一系列可编程 USB 集线器，支持按通道控制电源；部分型号支持数据线控制，部分型号支持电压/电流检测。该系列产品适用于开发、自动化测试和设备管理。

## 产品文档

| 产品名称 | 型号 / 订购代码 | 通道数量 | USB 规格 | 使用指南 | 技术规格书 |
| --- | --- | ---: | --- | --- | --- |
| SmartUSBHub Pro 4CH USB2.0 | `HBP_USB2_4CH`、`HBP_USB2_4CH_PSU` | 4 | USB 2.0 High-Speed | [使用指南](./products/usb2_4p/user_guide_cn.md) | [技术规格书](./products/usb2_4p/datasheet_cn.md) |
| SmartUSBHub Pro 7CH USB2.0 | `HBP_USB2_7CH`、`HBP_USB2_7CH_ADV` | 7 | USB 2.0 High-Speed | [使用指南](./products/usb2_7p/user_guide_cn.md) | [技术规格书](./products/usb2_7p/datasheet_cn.md) |

## 功能对照

| 产品 | 独立电源控制 | USB2.0 数据线控制 | 电压/电流检测 | BC 1.2 CDP | 本地通道按键 |
| --- | --- | --- | --- | --- | --- |
| SmartUSBHub Pro 4CH USB2.0 | 支持 | 支持 | 支持 | 支持，最大 1.5 A | 支持 |
| SmartUSBHub Pro 7CH USB2.0 | 支持 | 支持 | ADV 版本支持 | 支持 | 不支持 |

## 开发者文档

- 快速上手：[../README_cn.md#快速上手](../README_cn.md#快速上手)
- 通信协议：[SmartUSBHub 通信协议](./protocol_cn.md)
- Python 库说明：[../README_cn.md](../README_cn.md)
- Python 示例说明：[../examples/README_cn.md](../examples/README_cn.md)
