# SmartUSBHub 示例程序使用指南

本文档介绍 `examples` 目录下所有示例程序的用法和现象效果。

## 目录

- [基础示例](#基础示例)
  - [setting_example.py](#setting_examplepy---基础设置和信息查询)
  - [power_control_example.py](#power_control_examplepy---电源控制示例)
  - [voltage_monitor_example.py](#voltage_monitor_examplepy---电压监控示例)
  - [current_monitor_example.py](#current_monitor_examplepy---电流监控示例)
  - [dataline_control_example.py](#dataline_control_examplepy---数据线控制示例)
- [高级示例](#高级示例)
  - [multi_device_chasing_light.py](#multi_device_chasing_lightpy---多设备流水灯效果)
  - [multi_thread_example.py](#multi_thread_examplepy---多线程压力测试)
  - [multi_process_example.py](#multi_process_examplepy---多进程压力测试)
  - [reboot_example.py](#reboot_examplepy---MCU重启测试)
- [充电模式示例](#充电模式示例)
  - [charge_mode_toggle_demo.py](#charge_mode_toggle_demopy---充电模式切换演示)
  - [battery_test_example.py](#battery_test_examplepy---电池测试示例)
- [其他示例](#其他示例)
  - [user_callback_example.py](#user_callback_examplepy---用户回调示例)
  - [reset_dongle_example.py](#reset_dongle_examplepy---Dongle复位示例)
  - [frame_generate.py](#frame_generatepy---协议帧生成工具)
  - [simple_serial.py](#simple_serialpy---简单串口通信)
- [特殊应用](#特殊应用)
  - [oscilloscope.py](#oscilloscopepy---示波器应用)
  - [iphone_power_test/](#iphone_power_test---iPhone电源测试)
  - [multiprocess_architecture/](#multiprocess_architecture---多进程架构)

---

## 基础示例

### setting_example.py - 基础设置和信息查询

**功能：** 演示如何获取设备信息、设置默认状态、配置按钮控制等基础功能。

**运行方法：**
```bash
python examples/setting_example.py
```

**现象效果：**
1. 扫描并连接第一个可用的 SmartUSBHub 设备
2. 显示设备信息（名称、端口、地址等）
3. 获取并显示硬件版本和固件版本
4. 演示设置默认电源状态
5. 演示设置默认数据线状态
6. 演示配置按钮控制功能
7. 演示自动恢复功能

**适用场景：**
- 初次使用库时的快速入门
- 了解设备的基本配置选项
- 测试设备连接和基本信息获取

---

### power_control_example.py - 电源控制示例

**功能：** 演示如何控制每个通道的电源开关。

**运行方法：**
```bash
python examples/power_control_example.py
```

**现象效果：**
1. 扫描并连接设备
2. 依次打开通道 1、2、3、4 的电源
3. 等待一段时间
4. 依次关闭所有通道的电源
5. 循环执行上述操作

**适用场景：**
- 学习基本的电源控制 API
- 测试电源开关功能
- 验证设备响应

---

### voltage_monitor_example.py - 电压监控示例

**功能：** 实时监控每个通道的电压值。

**运行方法：**
```bash
python examples/voltage_monitor_example.py
```

**现象效果：**
- 持续显示每个通道的电压值（单位：V）
- 格式：`Channel 1: 5.00 V | Channel 2: 5.00 V | Channel 3: 0.00 V | Channel 4: 0.00 V`
- 更新频率：约 10ms 一次
- 按 `Ctrl+C` 退出

**适用场景：**
- 实时监控设备电压
- 检测电源状态
- 调试电源相关问题

**注意：** 需要设备支持 ADC 功能（`PRODUCT_ENABLE_CH_ADC`）。

---

### current_monitor_example.py - 电流监控示例

**功能：** 实时监控每个通道的电流值。

**运行方法：**
```bash
python examples/current_monitor_example.py
```

**现象效果：**
- 持续显示每个通道的电流值（单位：A）
- 格式：`Channel 1: 0.50 A | Channel 2: 0.30 A | Channel 3: 0.00 A | Channel 4: 0.00 A`
- 更新频率：约 10ms 一次
- 按 `Ctrl+C` 退出

**适用场景：**
- 实时监控设备电流
- 检测负载状态
- 调试电流相关问题

**注意：** 需要设备支持 ADC 功能（`PRODUCT_ENABLE_CH_ADC`）。

---

### dataline_control_example.py - 数据线控制示例

**功能：** 演示如何控制 USB 数据线的连接和断开。

**运行方法：**
```bash
python examples/dataline_control_example.py
```

**现象效果：**
1. 扫描并连接设备
2. 演示 USB2.0 数据线控制（如果支持）
3. 演示 USB3.0 数据线控制（如果支持）
4. 依次连接和断开数据线

**适用场景：**
- 学习数据线控制 API
- 测试数据线切换功能
- 验证 USB 数据连接

**注意：** 需要设备支持 USB2/USB3 数据线切换功能。

---

## 高级示例

### multi_device_chasing_light.py - 多设备流水灯效果

**功能：** 扫描并连接所有可用的 SmartUSBHub 设备，实现流水灯效果。

**运行方法：**
```bash
python examples/multi_device_chasing_light.py
```

**现象效果：**
1. 自动扫描并连接所有可用的设备
2. 显示每个设备的信息（端口、地址、硬件版本、固件版本）
3. 实现流水灯效果：
   - 按照设备顺序，依次打开每个设备的每个通道
   - 每个通道打开后保持一段时间
   - 然后关闭，继续下一个通道
   - 形成流水灯效果
4. 支持多个设备串联，形成更长的流水灯效果
5. 按 `Ctrl+C` 退出时，自动关闭所有通道

**适用场景：**
- 演示多设备控制
- 创建视觉效果展示
- 测试多设备协同工作

**特点：**
- 自动扫描所有设备
- 支持任意数量的设备
- 优雅的退出处理

---

### multi_thread_example.py - 多线程压力测试

**功能：** 使用多线程对多个设备进行并发压力测试。

**运行方法：**
```bash
python examples/multi_thread_example.py
```

**现象效果：**
1. 扫描并连接所有可用的设备
2. 显示每个设备的信息（端口、地址、硬件版本、固件版本）
3. 为每个设备的每个通道创建一个线程
   - 例如：4 个设备 × 4 个通道 = 16 个线程
4. 每个线程独立执行：
   - 打开通道电源
   - 检查电源状态
   - 关闭通道电源
   - 检查电源状态
   - 循环执行
5. 实时显示进度和成功/失败统计
6. 测试完成后显示每个通道的详细统计

**适用场景：**
- 压力测试和稳定性验证
- 测试多线程并发控制
- 验证设备在高并发场景下的表现

**特点：**
- 支持多设备多通道并发
- 实时进度显示
- 详细的统计信息
- 默认执行 1000 万次循环

**注意：** 建议在 `ENABLE_SYNC_LOCK = True` 的情况下使用，以确保线程安全。

---

### multi_process_example.py - 多进程压力测试

**功能：** 使用多进程架构对多个设备进行并发压力测试。

**运行方法：**
```bash
python examples/multi_process_example.py
```

**现象效果：**
1. 扫描所有可用的设备
2. 显示每个设备的信息（端口、地址、硬件版本、固件版本）
3. 为每个设备创建一个服务进程（管理串口连接）
4. 为每个设备的每个通道创建一个业务进程（执行测试）
   - 例如：4 个设备 × 4 个通道 = 4 个服务进程 + 16 个业务进程
5. 每个业务进程通过进程间通信访问对应的服务进程
6. 实时显示进度和成功/失败统计
7. 测试完成后显示每个通道的详细统计

**适用场景：**
- 多进程环境下的压力测试
- 测试多进程架构的稳定性
- 验证进程间通信机制

**特点：**
- 使用多进程架构，避免串口冲突
- 支持多设备多通道并发
- 实时进度显示
- 详细的统计信息
- 默认执行 1000 万次循环

**与多线程版本的区别：**
- 多线程版本：所有线程在同一进程中，共享 SmartUSBHub 实例
- 多进程版本：每个设备有独立的服务进程，通过进程间通信访问设备

---

### reboot_example.py - MCU重启测试

**功能：** 反复重启 MCU，测试重启功能的稳定性。

**运行方法：**
```bash
python examples/reboot_example.py
```

**现象效果：**
1. 扫描并连接设备
2. 显示设备信息
3. 循环执行重启操作：
   - 显示重启前的状态
   - 发送重启命令
   - 等待 MCU 重启（约 100ms）
   - 断开连接
   - 等待设备重新枚举（约 1.5-2 秒）
   - 重新连接设备
   - 显示重启后的状态
4. 显示重启次数和状态
5. 按 `Ctrl+C` 退出

**适用场景：**
- 测试 MCU 重启功能
- 验证设备重启后的恢复能力
- 测试 USB 设备重新枚举

**特点：**
- 自动处理设备断开和重连
- 显示每次重启的详细信息
- 默认最多执行 10 次重启（可配置）

---

## 充电模式示例

### charge_mode_toggle_demo.py - 充电模式切换演示

**功能：** 定时在快充和慢充模式之间切换。

**运行方法：**
```bash
python examples/charge_mode_toggle_demo.py
```

**现象效果：**
1. 扫描并连接设备
2. 每 4 秒在快充和慢充模式之间切换一次
3. 显示当前充电模式
4. 统计 "No ACK" 错误次数
5. 按 `Ctrl+C` 退出时显示统计信息

**适用场景：**
- 演示充电模式切换功能
- 测试充电模式稳定性
- 验证快充/慢充切换

**特点：**
- 自动统计错误次数
- 显示详细的错误信息
- 支持优雅退出

---

### battery_test_example.py - 电池测试示例

**功能：** 电池充放电测试。

**运行方法：**
```bash
python examples/battery_test_example.py
```

**现象效果：**
- 演示电池充放电测试流程
- 控制电源开关进行充放电循环
- 监控电压和电流变化

**适用场景：**
- 电池充放电测试
- 验证充电功能
- 测试电池管理

---

## 其他示例

### user_callback_example.py - 用户回调示例

**功能：** 演示如何使用用户回调函数。

**运行方法：**
```bash
python examples/user_callback_example.py
```

**现象效果：**
- 注册用户回调函数
- 当设备状态变化时触发回调
- 演示回调函数的使用方法

**适用场景：**
- 学习回调函数的使用
- 实现事件驱动的应用
- 响应设备状态变化

---

### reset_dongle_example.py - Dongle复位示例

**功能：** 演示如何复位 USB Dongle 设备。

**运行方法：**
```bash
python examples/reset_dongle_example.py
```

**现象效果：**
- 复位连接的 USB Dongle 设备
- 演示复位功能的使用

**适用场景：**
- 测试 USB Dongle 复位功能
- 调试 USB 设备问题

---

### frame_generate.py - 协议帧生成工具

**功能：** 生成协议帧的工具脚本。

**运行方法：**
```bash
python examples/frame_generate.py
```

**现象效果：**
- 生成各种协议帧
- 用于调试和测试

**适用场景：**
- 协议调试
- 生成测试数据
- 理解协议格式

---

### simple_serial.py - 简单串口通信

**功能：** 演示简单的串口通信。

**运行方法：**
```bash
python examples/simple_serial.py
```

**现象效果：**
- 基本的串口通信示例
- 发送和接收数据

**适用场景：**
- 学习串口通信
- 调试串口问题

---

## 特殊应用

### oscilloscope.py - 示波器应用

**功能：** 基于 SmartUSBHub 的示波器应用。

**运行方法：**
```bash
python examples/oscilloscope.py
```

**现象效果：**
- 图形化界面显示电压和电流波形
- 实时监控通道状态
- 支持数据记录和导出

**适用场景：**
- 实时监控电压/电流波形
- 数据分析和记录
- 设备调试

**注意：** 需要安装 GUI 库（如 PyQt5 或 tkinter）。

---

### iphone_power_test/ - iPhone电源测试

**功能：** iPhone 电源循环测试和电池监控。

**文件：**
- `iphone_power_cycle_test.py` - iPhone 电源循环测试
- `battery_plotter.py` - 电池数据绘图工具

**运行方法：**
```bash
python examples/iphone_power_test/iphone_power_cycle_test.py
```

**现象效果：**
- 对 iPhone 进行电源循环测试
- 监控电池状态
- 记录测试数据
- 生成测试报告

**适用场景：**
- iPhone 电源测试
- 电池充放电测试
- 设备兼容性测试

---

### multiprocess_architecture/ - 多进程架构

**功能：** 完整的多进程架构实现，解决多进程访问串口时的 ACK 错误问题。

**主要文件：**
- `run_all.py` - 主启动脚本
- `smartusbhub_server.py` - 服务进程
- `smartusbhub_client.py` - 客户端代理
- `business_process_*.py` - 业务进程示例
- `success_rate_test.py` - 成功率测试

**运行方法：**
```bash
python examples/multiprocess_architecture/run_all.py
```

**现象效果：**
- 启动 1 个服务进程（管理 USB 操作）
- 启动 4 个业务进程（每个控制一个通道）
- 所有 USB 操作在服务进程中串行执行
- 避免多进程竞争导致的 ACK 错误

**适用场景：**
- 多进程环境下的设备控制
- 解决多进程串口冲突问题
- 高并发场景下的稳定性测试

**详细文档：**
- `README.md` - 架构说明
- `QUICK_START.md` - 快速开始
- `TECHNICAL_EXPLANATION.md` - 技术详解
- `INTEGRATION_GUIDE.md` - 集成指南

---

## 使用建议

### 1. 首次使用
建议从 `setting_example.py` 开始，了解基本的设备连接和信息获取。

### 2. 学习电源控制
运行 `power_control_example.py` 学习基本的电源控制 API。

### 3. 多设备控制
如果有多个设备，可以运行 `multi_device_chasing_light.py` 查看多设备控制效果。

### 4. 压力测试
- 单进程多线程：使用 `multi_thread_example.py`
- 多进程：使用 `multi_process_example.py`

### 5. 实时监控
- 电压监控：`voltage_monitor_example.py`
- 电流监控：`current_monitor_example.py`

### 6. 特殊功能
- 充电模式：`charge_mode_toggle_demo.py`
- MCU 重启：`reboot_example.py`

---

## 注意事项

1. **设备连接**
   - 确保设备已正确连接并识别
   - 检查串口权限（Linux/macOS 可能需要 sudo）

2. **功能支持**
   - 某些功能需要设备支持相应的硬件特性
   - 例如：ADC 功能需要 `PRODUCT_ENABLE_CH_ADC`

3. **并发控制**
   - 多线程/多进程示例建议在 `ENABLE_SYNC_LOCK = True` 时使用
   - 多进程架构可以避免串口冲突

4. **退出程序**
   - 大部分示例支持 `Ctrl+C` 优雅退出
   - 退出时会自动关闭所有通道并断开连接

5. **错误处理**
   - 如果出现 "No Smart USB Hub found"，检查：
   - 设备是否已连接
   - 串口是否被其他程序占用
   - 设备驱动是否正常

---

## 常见问题

**Q: 运行示例时提示 "No Smart USB Hub found"**
A: 检查设备连接、串口权限，确保没有其他程序占用设备。

**Q: 多线程/多进程示例出现 ACK 错误**
A: 确保 `ENABLE_SYNC_LOCK = True`，或使用多进程架构。

**Q: 电压/电流监控显示 "N/A"**
A: 检查设备是否支持 ADC 功能，以及通道是否已打开电源。

**Q: 如何修改示例参数**
A: 直接编辑示例文件，修改相应的参数（如延迟时间、迭代次数等）。

---

## 更多信息

- 详细 API 文档：查看 `smartusbhub.py` 中的文档字符串
- 使用指南：`document/smartusbhub_user_guide.md`
- 更新日志：`CHANGELOG.md`

---

**最后更新：** 2024-12-28

