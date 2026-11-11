# 更新日志

[English](./CHANGELOG.md)

## [1.3.0] - 2026-11-11

### 新增

- 支持 USB3.0 四口基础版/ADV：设备能力识别、USB2.0/USB3.0 数据控制与 Host1/Host2 选择，产品家族编号为 `0x04`。
- 新增 `get_capability()`，返回合并已声明详情的能力文档，涵盖测量规格、设备与告警分组。
- 新增 `get_protocol_info()`，返回协议 API 版本、来源和升级建议。
- 新增全通道状态聚合查询。设备声明 `channel_status_mask=true` 时，电源、USB2.0、USB3.0 状态查询自动使用 `0x36`～`0x38` 聚合指令。
- 新增全通道默认配置聚合查询。设备声明 `device.default_status_mask=true` 时，默认电源、USB2.0、USB3.0 查询自动使用 `0x39`～`0x3B`。
- 新增 USB2.0/USB3.0 默认配置接口 `set/get_default_usb2_dataline_status()`、`set/get_default_usb3_dataline_status()`，以及按 `device.reset_hub` 能力提供的 `reset_hub()`。
- 新增 `supports_measurement_capture()` 与采样率查询/设置 `get/set_measurement_sample_rate()`、`get/set_measurement_filter()`，支持 10/100/250 Sa/s 档位，默认 250 Sa/s。
- 新增批量采集，支持瞬时与八点平均两种模式，批次含设备时间戳、序号、转换计数、统计及四路电压、电流和功率。
- 新增阈值告警接口 `get/set_alert_config()`、`get_alert_defaults()`、`get_alert_status()`、`clear_alert_latch()`、`reset_protection_trip()` 和 `subscribe_alert_events()`，使用设备声明的单位、范围和默认值。
- 新增单通道功率查询 `get_channel_power()`、缓存读取 `get_cached_measurements()` 和系统温度请求 `request_board_temperature()`。
- `register_callback()` 支持注册意外断连回调。
- 设备信息增加协议版本、来源及升级建议，旧固件设备连接时收到 `FirmwareUpdateRecommendedWarning` 升级提示。
- 新增模块级 `detect_v3_header_length()`（帧格式发现）与 `decode_usb3_capture_batch()`（采集批次解析）。

### 变更

- 变长协议帧格式更新：使用 16 字节帧头、请求编号和状态码。
- 电源、USB2.0、USB3.0 状态与默认配置查询按设备能力自动选择聚合或逐通道路径，返回类型与 PyPI 1.2.1 兼容；聚合回复同步全通道缓存并触发逐通道状态回调。
- 新默认配置接口返回 `{channel: {"enabled": 0/1, "value": 0/1}}`。
- HBP_USB2_4CH 的基础控制和测量继续使用原有路径，多通道测量可回退为逐路电压/电流查询。
- 流式测量与批量采集共用停流/恢复协调，切换采样率或滤波时自动生效。
- 示例整理为快速上手、单次测量和多设备控制三个主入口。
- 整理源码 docstring 和 API 行为说明，统一 SDK 源码、示例、脚本及测试的版权与 SPDX 许可证声明。
- 参数存储格式升级为格式 3，固件启动时自动迁移并保留原有配置。
- 移除 `supports_500sa_capture()`，批量采集能力改用 `supports_measurement_capture()` 和 `supported_sample_rates()` 判断。
- 以下接口改为兼容别名并发出 `LegacyAPIWarning` (`FutureWarning`)：`scan_and_connect_by_address()` → `scan_and_connect()`、`set_channel_dataline()`/`get_channel_dataline_status()` → USB2.0 命名接口、`set_default_dataline_status()`/`get_default_dataline_status()` → USB2.0 命名接口、`get_latest_measurements()` → `get_cached_measurements()`、`register_disconnect_callback()` → `register_callback()`。

- 正式兼容基线为 PyPI 1.2.1，保留其 55 个公开方法的名称、签名及绑定方式。七个旧入口默认提示 legacy 和迁移目标，同一调用位置通常提示一次。未交付的中途名称不保留别名。

### 修复

- 补齐协议文档 CRC 测试向量中缺失的保留字节。
- 持久化设置遇到固件保存拒绝时返回 `False`，保留原默认配置、名称和别名缓存。地址设置核对成功回显，保留 `0xFFFF` 合法地址，固件保存失败时通过超时返回失败。
- 修复重复控制/测量通道导致掩码进位、误选其他端口；控制参数无效时在保护操作和串口发送前拒绝。
- 电源及互锁命令收到固件明确拒绝时返回 `False`；配套固件对 GPIO 写入失败沿用既有失败回复，部分执行的通道不自动回滚。
- 重复或并发断开旧实例不再释放后续新连接的端口锁。
- 不等待 ACK 的 V3 测量流请求独立到期清理，丢回复后可重试，迟到回复不能完成新请求。

- 修复默认电源和默认 USB2.0 配置查询收到首帧后提前返回的问题，清理旧缓存并等待完整的 `enabled/value` 对。
- 多通道查询去重输入通道，避免重复通道叠加位掩码。
- 修复采集流的功率缓存同步，补齐功率字段解析和帧长度校验。
- 改进请求/响应匹配与主动流分发。
- 改进断连清理，串口 flush 失败后仍关闭句柄并释放连接注册。

## [1.2.2] - 2026-08-01 （未交付的开发记录）

### 新增

- 新增不打开串口的结构化 USB 描述符发现接口  
  `SmartUSBHub.scan_candidates()`。
- 新增公开的 `get_identity()` 与 `get_capabilities()` 元数据接口。
- 新增 `PortPermissionError`，调用方可区分权限不足与串口被占用。

### 变更

- 修正 7 通道产品型号的测量与过流能力元数据。

## [1.2.1] - 2026-07-27

### 变更

- 最低 Python 版本由 3.9 降至 3.7；SDK 未使用 Python 3.9 专属语言特性。
- 根目录 `requirements.txt` 现在只包含核心运行依赖 `pyserial`。GUI Demo  
  的可选依赖独立放在 `examples/requirements.txt`，且不再出现在包元数据中。
- 源码发行包现在会包含文档中列出的 Demo 及其独立可选依赖文件。
- 构建要求降至 `setuptools>=61`，同时确保 wheel 继续包含 `LICENSE` 和  
  `NOTICE`。

## [1.2.0] - 2026-07-16

### 变更

- 固件版本字符串改为不补零的 `V<主>.<次>` 格式（如 `V2.1`）。
- 移除非核心的多进程 broker；多进程共享设备需由应用层通过 IPC 实现。

### 修复

- 改进损坏 V3 帧的处理，避免阻塞后续帧解析。
- 修正 USB3 4CH 和 USB2 2CH 的能力信息。
- 补全发布包的 `NOTICE` 和 `smartusbhub.__version__`。
- 修正 2CH 集成测试的跳过逻辑。

## [1.1.0] - 2026-06-23

首个开源正式版本，兼容 1.0 的公开 API。

### 新增

- 支持安装为 `smartusbhub` 包，并加入 Apache-2.0 LICENSE、NOTICE 和完整测试。
- 新增 V3 协议、流式电压/电流测量和多型号能力识别。
- 扩展设备连接、测量、过流保护、命名、识别和重启等 API。
- 新增多进程 broker 和常用示例。

### 变更与修复

- 改进串口同步、节流和设备信息重试，提高稳定性。
- 精简依赖，并保留旧数据线方法作为兼容别名。
- 移除开发期的充电模式功能。
- 修复默认状态初始化及 V2 默认电源状态解析问题。

## [1.0.0] - 2024-07-01

初始版本，支持通道电源/数据控制、电压电流读取和基础配置。
