# SmartUSBHub API Coverage Matrix

This matrix tracks release-test coverage for the public Python SDK API.

Legend:

- Unit: offline pytest coverage, no device required. Includes the in-process
  device simulator (`test/unit/fake_device.py`), which drives the real SDK
  (send → encode → receive thread → parse → dispatch → ACK) against a faked
  serial link, so most command round-trips are now verified offline.
- Integration: real-device pytest coverage (`test/SmartUSBHub_Pro/tests/`).
- Manual: requires a load, multiple devices, reboot timing, or destructive state.

Offline line coverage of `smartusbhub.py` is ~70% (`python -m coverage run -m
pytest test/unit && python -m coverage report -m smartusbhub.py`). The remaining
gap is mostly the cross-process port-lock file handling and MCU error-recovery
branches.

| API area | APIs | Unit | Integration | Manual / notes |
| --- | --- | --- | --- | --- |
| Discovery / connection | `scan_available_ports`, `scan_and_connect`, `scan_and_connect_by_address`, `auto_connect`, `disconnect`, `close`, `is_connected` | port enumeration faked: scan/scan-by-address/auto-connect happy + miss paths, feature filter, lifecycle failure cleanup | real device: scan/auto-connect, by-address match + mismatch (`test_integration_discovery.py`) | multi-device address scan still needs a second device |
| Device information | `get_device_info`, `get_firmware_version`, `get_hardware_version`, `get_product_type`, `get_product_name`, `get_max_channels`, `get_serial_no`, `get_channels`, `get_product_info` | full identity handshake against simulator, product table, channel resolution, `get_product_info` lookup | device info/version/serial/channel count | product matrix should be repeated for every released model |
| Power control | `set_channel_power`, `get_channel_power_status`, `set_channel_power_interlock` | loopback set/get round-trip, interlock, multi-channel, mask conversion, frame parsing, encoder byte assertions | single channel, all channels, combinations, odd/even `0x55`, interlock | long-run relay/power cycling covered by stress tests |
| USB2 data-line control | `set_channel_usb2_dataline`, `get_channel_usb2_dataline_status` | loopback set/get round-trip, frame parsing | single channel and all channels when supported | needs USB enumeration fixture for data continuity verification |
| Voltage/current one-shot | `get_channel_voltage`, `get_channel_current` | loopback read, ADC unsupported/error paths, payload parsing, single-channel guard | every channel, powered before measurement | accuracy needs calibrated load/meters |
| Voltage/current batch | `get_channel_measurements` | loopback V3 batch read, payload parsing, cache snapshot | all-channel real-device batch read | accuracy needs calibrated load/meters |
| Voltage/current stream | `set_channel_measurement_stream`, `get_stream_channel_measurements`, `get_latest_measurements` | blocking stream read via simulator, stream-frame-does-not-set-ACK rule, V3 stream payload parsing | start/stop, blocking read, latest cache | long-run stream soak should be run before release |
| Overcurrent monitor | `get_channel_oc_status`, `clear_channel_oc_latch` | loopback query + latch clear, payload parsing, clear command arguments | query and clear command path | real overcurrent trigger requires protected load fixture |
| Device settings | `set_button_control`, `get_button_control_status`, `set_default_power_status`, `get_default_power_status`, `set_default_dataline_status`, `get_default_dataline_status`, `set_auto_restore`, `get_auto_restore_status`, `set_device_address`, `get_device_address`, `set_operate_mode`, `get_operate_mode` | loopback round-trip for all of these, address validation | button, auto-restore, address, default power, default data-line | persistence after reboot should be verified per release |
| Callbacks | `register_callback`, `register_disconnect_callback` | callback fires on ACK, unknown-command no-op, throwing-callback isolation, disconnect callback on serial error | callback on real ACK, disconnect-callback registration (`test_integration_discovery.py`) | — |
| Receive loop / framing | (internal) `_uart_recv_task` dispatch | split-frame reassembly, two-frames-per-read, leading-garbage skip, stream vs ACK | exercised implicitly by every integration test | — |
| Factory / reboot | `factory_reset`, `reboot_mcu` | loopback ACK for both, lifecycle cleanup | factory reset in fixture teardown; `reboot_mcu` + reconnect (`test_integration_discovery.py`) | physical power-loss recovery still manual |
