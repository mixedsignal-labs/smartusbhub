# SmartUSBHub 示例程序使用指南

本文档介绍 `examples` 目录下所有示例程序的用法和现象效果。

## 目录结构

```
examples/
├── SmartUSBHub_Pro/          # SmartUSBHub Pro 产品示例
│   ├── 基础示例
│   │   ├── setting_example.py              # 基础设置和信息查询
│   │   ├── power_control_example.py        # 电源控制示例
│   │   ├── dataline_control_example.py      # 数据线控制示例
│   │   └── user_callback_example.py        # 用户回调示例
│   ├── 监控示例
│   │   ├── voltage_monitor_example.py       # 电压监控示例
│   │   └── current_monitor_example.py       # 电流监控示例
│   ├── 充电模式示例
│   │   ├── charge_mode_toggle_demo.py       # 充电模式切换演示
│   │   ├── battery_test_example.py         # 电池测试示例
│   │   └── auto_charge_mode_switch.py      # 自动充电模式切换
│   ├── 高级示例
│   │   ├── multi_device_chasing_light.py   # 多设备流水灯效果
│   │   └── oscilloscope.py                 # 示波器应用
│   └── 特殊应用
│       └── iphone_power_test/              # iPhone电源测试
│
├── FlexConnect/              # FlexConnect 产品示例
│   ├── flexconnect_mode_switch_demo.py     # 模式切换演示
│   └── diagnose_params.py                  # 参数诊断工具
│
└── Common/                   # 通用示例和工具
    ├── simple_serial.py                     # 简单串口通信
    └── multiprocess_architecture/          # 多进程架构
```

## 快速开始

### SmartUSBHub Pro 示例

#### 基础示例

```bash
# 基础设置和信息查询
python examples/SmartUSBHub_Pro/setting_example.py

# 电源控制示例
python examples/SmartUSBHub_Pro/power_control_example.py

# 数据线控制示例
python examples/SmartUSBHub_Pro/dataline_control_example.py

# 用户回调示例
python examples/SmartUSBHub_Pro/user_callback_example.py
```

#### 监控示例

```bash
# 电压监控（实时显示电压值）
python examples/SmartUSBHub_Pro/voltage_monitor_example.py

# 电流监控（实时显示电流值）
python examples/SmartUSBHub_Pro/current_monitor_example.py
```

#### 充电模式示例

```bash
# 充电模式切换演示
python examples/SmartUSBHub_Pro/charge_mode_toggle_demo.py

# 电池测试示例
python examples/SmartUSBHub_Pro/battery_test_example.py

# 自动充电模式切换
python examples/SmartUSBHub_Pro/auto_charge_mode_switch.py
```

#### 高级示例

```bash
# 多设备流水灯效果
python examples/SmartUSBHub_Pro/multi_device_chasing_light.py

# 示波器应用（图形界面）
python examples/SmartUSBHub_Pro/oscilloscope.py
```

### FlexConnect 示例

```bash
# 模式切换演示
python examples/FlexConnect/flexconnect_mode_switch_demo.py

# 参数诊断工具
python examples/FlexConnect/diagnose_params.py
```

**注意：** FlexConnect 的测试文件已移动到 `test/FlexConnect/` 目录，请使用测试框架运行测试。

### 通用示例

```bash
# 简单串口通信
python examples/Common/simple_serial.py

# 多进程架构
python examples/Common/multiprocess_architecture/run_all.py
```

## 详细说明

### SmartUSBHub Pro 示例

#### 基础示例

##### setting_example.py - 基础设置和信息查询

**功能：** 演示如何获取设备信息、设置默认状态、配置按钮控制等基础功能。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/setting_example.py
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

##### power_control_example.py - 电源控制示例

**功能：** 演示如何控制每个通道的电源开关。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/power_control_example.py
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

##### dataline_control_example.py - 数据线控制示例

**功能：** 演示如何控制 USB 数据线的连接和断开。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/dataline_control_example.py
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

##### user_callback_example.py - 用户回调示例

**功能：** 演示如何使用用户回调函数。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/user_callback_example.py
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

#### 监控示例

##### voltage_monitor_example.py - 电压监控示例

**功能：** 实时监控每个通道的电压值。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/voltage_monitor_example.py
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

##### current_monitor_example.py - 电流监控示例

**功能：** 实时监控每个通道的电流值。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/current_monitor_example.py
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

#### 充电模式示例

##### charge_mode_toggle_demo.py - 充电模式切换演示

**功能：** 定时在快充和慢充模式之间切换。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/charge_mode_toggle_demo.py
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

---

##### battery_test_example.py - 电池测试示例

**功能：** 电池充放电测试。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/battery_test_example.py
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

#### 高级示例

##### multi_device_chasing_light.py - 多设备流水灯效果

**功能：** 扫描并连接所有可用的 SmartUSBHub 设备，实现流水灯效果。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/multi_device_chasing_light.py
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

---

##### oscilloscope.py - 示波器应用

**功能：** 基于 SmartUSBHub 的示波器应用。

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/oscilloscope.py
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

#### 特殊应用

##### iphone_power_test/ - iPhone电源测试

**功能：** iPhone 电源循环测试和电池监控。

**文件：**
- `iphone_power_cycle_test.py` - iPhone 电源循环测试
- `battery_plotter.py` - 电池数据绘图工具

**运行方法：**
```bash
python examples/SmartUSBHub_Pro/iphone_power_test/iphone_power_cycle_test.py
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

### FlexConnect 示例

#### flexconnect_mode_switch_demo.py - 模式切换演示

**功能：** 演示 FlexConnect 产品的模式切换功能。

**运行方法：**
```bash
python examples/FlexConnect/flexconnect_mode_switch_demo.py
```

**现象效果：**
- 按回车键循环切换 FlexConnect 模式：PC -> UDISK1 -> UDISK2 -> PC -> ...
- 显示当前模式和故障状态
- 输入 'q' 退出程序

**适用场景：**
- 演示模式切换功能
- 快速测试模式切换
- 验证设备响应

---

#### diagnose_params.py - 参数诊断工具

**功能：** 诊断 FlexConnect 设备的参数设置，用于排查掉电恢复逻辑问题。

**运行方法：**
```bash
python examples/FlexConnect/diagnose_params.py
```

**现象效果：**
- 读取并显示所有相关参数
- 显示当前模式、默认模式、掉电恢复状态等
- 用于调试和排查问题

**适用场景：**
- 排查掉电恢复逻辑问题
- 调试设备参数设置
- 验证参数持久化

**注意：** 如需运行 FlexConnect 的完整测试，请使用 `test/FlexConnect/` 目录下的测试文件。

---

### 通用示例

#### simple_serial.py - 简单串口通信

**功能：** 演示简单的串口通信。

**运行方法：**
```bash
python examples/Common/simple_serial.py
```

**现象效果：**
- 基本的串口通信示例
- 发送和接收数据

**适用场景：**
- 学习串口通信
- 调试串口问题

---

#### multiprocess_architecture/ - 多进程架构

**功能：** 完整的多进程架构实现，解决多进程访问串口时的 ACK 错误问题。

**主要文件：**
- `run_all.py` - 主启动脚本
- `smartusbhub_server.py` - 服务进程
- `smartusbhub_client.py` - 客户端代理
- `business_process_*.py` - 业务进程示例
- `success_rate_test.py` - 成功率测试

**运行方法：**
```bash
python examples/Common/multiprocess_architecture/run_all.py
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
建议从 `SmartUSBHub_Pro/setting_example.py` 开始，了解基本的设备连接和信息获取。

### 2. 学习电源控制
运行 `SmartUSBHub_Pro/power_control_example.py` 学习基本的电源控制 API。

### 3. 多设备控制
如果有多个设备，可以运行 `SmartUSBHub_Pro/multi_device_chasing_light.py` 查看多设备控制效果。

### 4. 实时监控
- 电压监控：`SmartUSBHub_Pro/voltage_monitor_example.py`
- 电流监控：`SmartUSBHub_Pro/current_monitor_example.py`

### 5. 特殊功能
- 充电模式：`SmartUSBHub_Pro/charge_mode_toggle_demo.py`
- FlexConnect模式：`FlexConnect/flexconnect_mode_switch_demo.py`

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
