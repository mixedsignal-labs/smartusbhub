# Changelog

[简体中文](./CHANGELOG_cn.md)

## [1.3.1] - 2026-11-12

### Fixed

- Decode older V3 measurement payloads with four-byte voltage/current records, including shipped seven-port firmware, while retaining eight-byte records with hardware power. Clear unavailable hardware-power cache entries so `get_channel_power()` can use voltage/current fallback.
- Accept empty or matching one-byte acknowledgements for streaming enable/disable requests. Unsolicited samples cannot acknowledge a command, and a later one-shot query still requires a complete measurement payload.
- Reject malformed or truncated measurement replies without reporting success, changing valid cached measurements or publishing a stream sample.

### Compatibility

- Public API signatures, runtime dependencies and the protocol API version are unchanged from 1.3.0. Existing 1.3.0 scripts can upgrade without changes.

## [1.3.0] - 2026-11-11

### Added

- USB3.0 four-port BASIC/ADV support: device capability identification, USB2.0/USB3.0 data control and Host1/Host2 selection, with product family ID `0x04`.
- `get_capability()` returns the capability document with advertised measurement, device and alert details merged.
- `get_protocol_info()` reports the protocol API version, source and upgrade advice.
- Whole-device status aggregation. When `channel_status_mask=true`, power/USB2.0/USB3.0 status getters automatically use aggregate commands `0x36`–`0x38`.
- Whole-device default configuration aggregation. When `device.default_status_mask=true`, default power/USB2.0/USB3.0 getters automatically use `0x39`–`0x3B`.
- Explicit USB2.0/USB3.0 default configuration APIs `set/get_default_usb2_dataline_status()` and `set/get_default_usb3_dataline_status()`, plus `reset_hub()` gated by `device.reset_hub`.
- `supports_measurement_capture()` and sample-rate query/configuration through `get/set_measurement_sample_rate()` and `get/set_measurement_filter()`, with 10/100/250 Sa/s rates and a 250 Sa/s default.
- Batched capture with instantaneous and eight-conversion-average modes; batches include device timestamps, sequence/conversion counters, statistics and four-channel voltage/current/power.
- Threshold alert APIs `get/set_alert_config()`, `get_alert_defaults()`, `get_alert_status()`, `clear_alert_latch()`, `reset_protection_trip()` and `subscribe_alert_events()`, using device-declared units, ranges and defaults.
- Single-channel power queries through `get_channel_power()`, cache access through `get_cached_measurements()` and system-temperature requests through `request_board_temperature()`.
- `register_callback()` registers an unexpected-disconnection callback.
- Device information now includes protocol version, source and upgrade advice; older firmware receives a `FirmwareUpdateRecommendedWarning` once per connection.
- Module-level `detect_v3_header_length()` (framing discovery) and `decode_usb3_capture_batch()` (capture batch decoding).

### Changed

- Updated variable-length protocol framing: a 16-byte header with request IDs and status codes, discovered through read-only commands.
- Power, USB2.0 and USB3.0 status and default getters automatically select aggregate or per-channel paths by device capability. Return types remain compatible with PyPI 1.2.1; aggregate replies update every channel cache and invoke per-channel status callbacks.
- New default configuration APIs return `{channel: {"enabled": 0/1, "value": 0/1}}`.
- Shipped HBP_USB2_4CH keeps the legacy control/measurement path, with per-channel voltage/current fallback for multi-channel measurements.
- Streaming and batched capture share stream stop/restart coordination; sample-rate and filter changes take effect automatically.
- Examples are reorganized into three main entry points: quick start, one-shot measurement and multi-device control.
- Clarified source docstrings and API behavior notes, and standardized copyright and SPDX headers across SDK code, examples, scripts and tests.
- Companion firmware migrates parameter-storage format 3 at startup and preserves existing settings.
- `supports_500sa_capture()` is removed; use `supports_measurement_capture()` and `supported_sample_rates()` for batch capture support and individual rates.
- The following APIs remain as compatibility aliases emitting `LegacyAPIWarning` (`FutureWarning`): `scan_and_connect_by_address()` → `scan_and_connect()`, `set_channel_dataline()`/`get_channel_dataline_status()` → USB2.0-named APIs, `set_default_dataline_status()`/`get_default_dataline_status()` → USB2.0-named APIs, `get_latest_measurements()` → `get_cached_measurements()`, `register_disconnect_callback()` → `register_callback()`.

- The compatibility baseline is PyPI 1.2.1. Its 55 public method names, signatures and bindings are retained. Seven legacy entry points emit a visible migration warning, normally once per call site. Unreleased transitional names have no aliases.

### Fixed

- Corrected a missing reserved byte in the protocol documentation's CRC test vector.
- Persistent configuration setters return `False` for firmware save rejections without replacing cached defaults, names or aliases. Address writes require a matching echo, preserve `0xFFFF` as a valid address and time out when firmware cannot save it.
- Fixed duplicate control/measurement channel masks selecting a different port; invalid control channels are rejected before protection or serial side effects.
- Power and interlock commands return `False` for explicit firmware rejection instead of treating any ACK as success. Companion firmware also reports GPIO write failures using the existing rejection reply; partially applied changes are not rolled back.
- Repeated/concurrent disconnect cleanup cannot release a later connection's port lock.
- No-wait V3 stream requests expire independently of `Event.wait()`, allowing retries after a lost ACK while rejecting late replies.

- Default power and default USB2.0 reads no longer return early after the first reply; stale cache entries are cleared and every requested `enabled/value` pair is awaited.
- Multi-channel queries deduplicate input channels before building masks.
- Capture streams update the power cache; power-field parsing and frame-length validation are complete.
- Improved request/reply matching and unsolicited-stream dispatch.
- Disconnection cleanup closes the port handle and releases registrations even after a flush failure.

## [1.2.2] - 2026-08-01 (unreleased development record)

### Added
- Added structured, non-opening USB descriptor discovery with
  `SmartUSBHub.scan_candidates()`.
- Added public `get_identity()` and `get_capabilities()` metadata APIs.
- Added `PortPermissionError` so callers can distinguish permission failures
  from ports that are already in use.

### Changed
- Corrected measurement and overcurrent capability metadata for 7-channel
  product variants.

## [1.2.1] - 2026-07-27

### Changed
- Lowered the minimum supported Python version from 3.9 to 3.7. The SDK does
  not use Python 3.9-specific language features.
- The root `requirements.txt` now contains only the core runtime dependency,
  `pyserial`. Optional GUI demo dependencies are isolated in
  `examples/requirements.txt` and are absent from the package metadata.
- Source distributions now include the documented examples and their separate
  optional requirements file.
- Lowered the build requirement to `setuptools>=61` while retaining both
  `LICENSE` and `NOTICE` in built wheels.

## [1.2.0] - 2026-07-16

### Changed
- Firmware version strings now use `V<major>.<minor>` without zero-padding
  (for example, `V2.1`).
- Removed the non-core multiprocess broker. Applications that share a device
  across processes should provide their own IPC broker.

### Fixed
- Improved malformed V3 frame handling so later frames are not blocked.
- Corrected capability metadata for USB3 4CH and USB2 2CH devices.
- Included `NOTICE` and exposed `smartusbhub.__version__` in release packages.
- Fixed integration-test skipping for unsupported 2CH data-line tests.

## [1.1.0] - 2026-06-23

First open-source release, compatible with the 1.0 public API.

### Added
- Installable `smartusbhub` package with Apache-2.0 licensing and tests.
- V3 protocol, streaming voltage/current measurements and model capabilities.
- APIs for connection, measurement, overcurrent protection, naming,
  identification and reboot.
- Multiprocess broker and common usage examples.

### Changed and Fixed
- Improved serial synchronization, throttling and device-info retries.
- Simplified dependencies and retained legacy data-line methods as aliases.
- Removed the development-only charge mode feature.
- Fixed default-state initialization and V2 default-power-state parsing.

## [1.0.0]

Initial release with per-channel power/data control, voltage/current readings
and basic configuration.
