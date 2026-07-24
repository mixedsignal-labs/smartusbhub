# SmartUSBHub Pro 7CH USB2.0 Technical Specifications

[简体中文](./datasheet_cn.md)

[Download PDF](./downloads/datasheet-en.pdf)

| Document item | Details |
| --- | --- |
| Applicable product | SmartUSBHub Pro 7CH USB2.0 |
| Order codes | `HBP_USB2_7CH`, `HBP_USB2_7CH_ADV` |
| Document version | v1.0 |
| Release date | 2026-07-23 |

## 1 Product Overview

SmartUSBHub Pro 7CH USB2.0 is a seven-port programmable USB 2.0 High-Speed hub. It independently controls VBUS and USB 2.0 D+ / D- on every downstream port for simulated hot-plugging, power cycling, enumeration-order control and fault recovery. The ADV variant also measures VBUS voltage and output current on every channel.

### 1.1 Model Differences

| Feature | `HBP_USB2_7CH` | `HBP_USB2_7CH_ADV` |
| --- | --- | --- |
| Independent VBUS control on seven ports | Yes | Yes |
| Independent D+ / D- control on seven ports | Yes | Yes |
| Overcurrent-status monitoring | Yes | Yes |
| Per-channel voltage/current measurement | No | Yes |
| Measurement streaming | No | Up to 100 Hz |

### 1.2 Key Features

- Seven USB-A downstream ports with independent VBUS and D+ / D- control.
- USB 2.0 High-Speed link rate up to 480 Mbps; compatible with Full-Speed, Low-Speed and USB 1.1 devices.
- Separate USB-C DATA and CMD interfaces isolate the data path from the control path.
- USB BC 1.2 CDP support with up to 1.5 A charging current per port; QC, USB PD and other fast-charging protocols are not supported.
- Approximately 2.1 A overcurrent-protection threshold and per-channel overcurrent-status monitoring.
- Per-channel voltage/current measurement on the ADV variant.
- Normal mode, interlock mode, default power and data-line states, restoration after power loss and configurable device address.

## 2 System Architecture

### 2.1 System Block Diagram

![Figure 2-1 SmartUSBHub Pro 7CH USB2.0 system block diagram](./assets/system_block_diagram.svg)

The DATA port carries hub traffic for all seven downstream ports. The CMD port enumerates as a USB CDC serial interface and receives control commands. The external DC input supplies the downstream ports through two 5 V power rails.

### 2.2 Interfaces and Indicators

| Interface or component | Quantity | Function |
| --- | ---: | --- |
| USB-C DATA | 1 | Connects to the USB host and carries downstream-device data |
| USB-C CMD | 1 | Connects to the control host and provides the USB CDC command interface |
| DC IN | 1 | DC5525, center-positive; accepts a protected DC supply |
| USB-A downstream ports | 7 | Connect controlled USB devices |
| Status indicator | 1 | Indicates device operating state |
| Channel indicators | 7 | Indicate the VBUS state of the corresponding channels |

## 3 Functional Specifications

### 3.1 USB Data Path

| Parameter | Specification |
| --- | --- |
| USB standard | USB 2.0 High-Speed |
| Maximum link rate | 480 Mbps |
| Compatible speeds | Full-Speed 12 Mbps, Low-Speed 1.5 Mbps, USB 1.1 |
| Upstream data port | 1 × USB-C |
| Downstream ports | 7 × USB-A |
| Hub mode | MTT / STT supported |

### 3.2 Channel Control

| Parameter | Specification |
| --- | --- |
| Channel numbers | CH1–CH7 |
| VBUS control | Independent on every downstream port |
| D+ / D- control | Independent on every downstream port |
| Power/data relationship | USB data can be disconnected while VBUS remains powered |
| Control methods | Single-channel, batch, normal and interlock control; only one channel can be enabled at a time in interlock mode |
| Default state and restoration | Configurable default power state, default data-line state and restoration after power loss |
| Local channel buttons | None |

### 3.3 Charging and Overcurrent Protection

| Parameter | Specification |
| --- | --- |
| Charging protocol | USB BC 1.2 CDP |
| BC 1.2 charging current | Up to 1.5 A per port |
| Per-port protection threshold | Approximately 2.1 A |
| Maximum total output current | 10 A shared by all seven ports |
| Overcurrent status | Readable per channel |
| Other fast-charging protocols | QC, USB PD and other fast-charging protocols are not supported |

### 3.4 Voltage and Current Measurement (ADV Variant)

| Parameter | Range | Resolution | Accuracy |
| --- | --- | --- | --- |
| VBUS voltage | 0–5.5 V per channel | 8 mV | ±32.5 mV at 5 V and 25 °C |
| Output current | 0–2.7 A per channel | 1 mA | ±(1.25% × reading + 2.5 mA) at 25 °C |
| Measurement stream | - | Up to 100 Hz | Depends on host and software configuration |

## 4 Electrical Specifications

:::{admonition} Warning: use only the specified DC supply
:class: warning

The normal input range is 9–20 V DC. Use a qualified 19–20 V / 5 A supply with current limiting and short-circuit protection. The 24.5 V absolute maximum is not an allowed operating voltage.
:::

### 4.1 Absolute Maximum Ratings

Exceeding these limits may permanently damage the device. Do not operate continuously near an absolute maximum rating.

| Parameter | Minimum | Maximum | Unit | Notes |
| --- | ---: | ---: | --- | --- |
| DC input voltage | 0 | 24.5 | V | Absolute maximum, not an operating rating |
| Downstream-port VBUS | 0 | 5.5 | V | USB-A downstream ports |
| USB D+ / D- signal voltage | -0.3 | 5.3 | V | USB signal pins |

### 4.2 Recommended Operating Conditions

| Parameter | Condition | Minimum | Typical | Maximum | Unit |
| --- | --- | ---: | ---: | ---: | --- |
| DC input voltage | External DC input | 9 | 19–20 | 20 | V |
| Recommended power adapter | Current-limited and short-circuit protected | - | 20 V / 5 A | - | - |
| 5 V output voltage | No load | 4.97 | 5.11 | 5.25 | V |
| Port VBUS | Typical 1.5 A load | 4.87 | 5.00 | 5.25 | V |
| Maximum total output current | All seven ports combined | - | - | 10 | A |
| Operating ambient temperature | Non-condensing | 0 | 25 | 50 | °C |
| Relative humidity | Non-condensing | 5 | - | 95 | %RH |
| Altitude | Indoor use | - | - | 2000 | m |

:::{admonition} Important: also account for the total device output current
:class: important

The approximately 2.1 A per-port threshold is a protection limit; it does not mean all seven ports can continuously supply that current. Combined output current must not exceed 10 A. Seven ports each drawing the USB BC 1.2 maximum of 1.5 A would require 10.5 A, which exceeds the device limit.
:::

## 5 Protection and Safety Limits

| Item | Specification |
| --- | --- |
| DC input | Input fuse and overvoltage protection |
| Per-port current limit | Approximately 2.1 A |
| Short-circuit and overtemperature protection | Supported; remove the faulty load and allow the unit to cool before recovery |
| Overcurrent-status signal | Monitored per channel |
| USB-signal ESD | Board-level ESD protection; certification level is subject to the formal test report |
| Fast-charging protocols | QC, USB PD and other fast-charging negotiation are not supported |

- Combined output current across all seven ports must not exceed 10 A.
- Maintain ventilation during prolonged operation near the maximum total output current. Do not cover the device or place it near flammable materials.
- Turning off VBUS or D+ / D- is equivalent to unplugging a device. Stop file writes, firmware updates and other non-interruptible operations first.
- This product is intended for USB automation testing and device control. Do not use it as the sole protective device in medical, life-safety, vehicle-safety or other high-safety-level systems.

## 6 Mechanical and Environmental Specifications

| Parameter | Specification |
| --- | --- |
| Dimensions | 84 mm × 56.8 mm × 28 mm |
| Device weight | Approximately 142 g |
| Enclosure material | Aluminum alloy |
| Mounting | Desktop placement; custom brackets can be used |
| Operating temperature | 0–50 °C, non-condensing |
| Storage temperature | -10–85 °C, non-condensing |
| Relative humidity | 5%–95% RH, non-condensing |
| Maximum operating altitude | 2000 m |

Allow room for cable bend radius, connector access and ventilation; do not design an installation only around the product envelope dimensions.

## 7 Related Documentation

| Document | Link |
| --- | --- |
| SmartUSBHub Pro 7CH USB2.0 User Manual | [View manual](./user_guide.md) |
| SmartUSBHub communication protocol | [View documentation](../../protocol.md) |
| SmartUSBHub documentation center | [View documentation](../../README.md) |
| SmartUSBHub Python library guide | [View documentation](../../../README.md) |
