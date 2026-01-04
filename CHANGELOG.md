# Changelog

## [Unreleased]

### Added
- **串口发送同步机制**：添加了 `_send_lock`、`_min_send_interval` (10ms) 和 `_mcu_response_wait` (5ms) 机制
  - 即使 `ENABLE_SYNC_LOCK = False` 时也保护串口发送，避免命令交错
  - 确保命令之间至少间隔 10ms，避免命令发送过快导致通信问题
  - 发送命令后等待 5ms，确保设备有时间处理命令并开始发送 ACK
- **设备信息获取重试机制**：添加了 `_retry_get_info()` 辅助函数
  - 所有关键设备信息（hardware_version, firmware_version, operate_mode 等）都会重试至少 10 秒
  - 自适应重试间隔：前 3 次 50ms，4-10 次 100ms，10 次以上 200ms
  - 提高初始化成功率，特别是在设备初始化或恢复期间

### Changed
- **`get_device_info()` 方法改进**：
  - 所有关键信息使用重试机制获取，确保至少尝试 10 秒
  - 改进了错误处理：如果获取默认状态失败，保持原有值（不覆盖为 None）
  - 移除了命令间的额外延迟，因为 `_send_packet` 中已经通过 `_min_send_interval` 和 `_mcu_response_wait` 确保了命令间隔
- **初始化流程优化**：
  - 在 `_start()` 后添加 150ms 延迟，等待设备初始化完成
  - 确保 `get_device_info()` 调用时设备已经准备好接收命令

### Fixed
- **字典初始化修复**：修复了 `TypeError: 'NoneType' object does not support item assignment` 错误
  - 将 `channel_default_power_flag`、`channel_default_power_status`、`channel_default_dataline_flag`、`channel_default_dataline_status` 初始化为空字典而不是 None
  - 确保即使 `get_default_power_status()` 失败，字典仍然可以安全访问
- **`get_default_power_status()` 协议修复**：修改数据发送格式，使用 V2 协议 `[0,0]` 作为 data 参数，确保协议一致性
- **错误处理改进**：在 `_handle_get_default_power_status` 和 `_handle_get_default_dataline_status` 中添加了 None 检查和错误日志

### Removed
- **移除 `reboot_mcu` 功能**：暂时移除了设备重启命令相关代码
  - 移除了 `CMD_REBOOT_MCU` 命令定义
  - 移除了 `ack_events` 中的 `CMD_REBOOT_MCU` 事件
  - 移除了 `_handle_reboot_mcu()` 方法
  - 移除了 `reboot_mcu()` 公共方法
- **移除 `get_device_info()` 中的冗余延迟**：移除了命令间的 `time.sleep(0.01)` 调用
  - 因为 `_send_packet` 中已经通过 `_min_send_interval` 和 `_mcu_response_wait` 确保了命令间隔
  - 避免重复延迟，提高代码效率和可读性