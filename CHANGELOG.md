# Changelog

[简体中文](./CHANGELOG_cn.md)

This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
