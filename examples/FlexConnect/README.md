# FlexConnect 示例程序

FlexConnect 产品的演示程序和工具脚本，从快速入门到高级自动化应用。

---

## 📋 文件列表

### 🚀 快速开始示例

| 文件 | 类型 | 说明 |
|-----|------|------|
| `basic_usage.py` | 入门示例 | 基础使用入门，演示连接、查询、切换等基本操作 |
| `flexconnect_mode_switch_demo.py` | 交互演示 | 交互式模式切换演示，循环切换各种模式 |

### 🎓 进阶示例

| 文件 | 类型 | 说明 |
|-----|------|------|
| `power_restore_demo.py` | 功能演示 | 掉电恢复功能完整演示，包含优先级测试 |

### 🚀 高级示例

| 文件 | 类型 | 说明 |
|-----|------|------|
| `automation_suite.py` | 自动化框架 | 完整的自动化测试套件，含 ADB 和 U 盘测试 |

### 🔧 诊断工具

| 文件 | 类型 | 说明 |
|-----|------|------|
| `diagnose_params.py` | 诊断工具 | 读取并显示所有相关参数，用于排查问题 |

---

## 🚀 快速开始

### 环境准备

1. **安装依赖**
   ```bash
   cd SmartUSBHub_Pro-4CH_USB2.0/library/smartusbhub_ng
   pip install -r requirements.txt
   pip install -e .
   ```

2. **硬件连接**
   - 连接 FlexConnect 设备到 PC
   - 确保可以通过 USB 转串口通信

---

## 📖 详细说明

### basic_usage.py - 基础使用入门

**功能：** 演示 FlexConnect 产品的基本使用方法。

**运行方法：**
```bash
python examples/FlexConnect/basic_usage.py
```

**演示内容：**
1. 扫描并连接设备
2. 获取设备信息（型号、版本、序列号等）
3. 查询当前状态（模式、掉电恢复、按键状态）
4. 模式切换演示（PC 模式 ↔ U 盘模式）
5. 验证切换结果

**适用场景：**
- 🎯 快速入门和学习
- 🎯 验证设备连接
- 🎯 基本功能测试
- 🎯 学习 API 使用方法

**预期输出：**
```
======================================================
FlexConnect 基础使用示例
======================================================

[步骤1] 扫描并连接设备...
✓ 成功连接到设备

[步骤2] 获取设备信息...
设备信息:
  产品名称: SmartUSBSwitch FlexConnect
  产品类型: 0x14
  硬件版本: v1.0
  固件版本: v1.0.0
  
[步骤3] 获取当前状态...
  当前模式: PC 模式（ADB 调试）
  掉电恢复: 已禁用
  按键控制: 已启用
  
[步骤4] 模式切换演示...
  → 切换到 PC 模式...
  ✓ 切换成功
  ✓ 验证成功: 当前为 PC 模式
  
✓ 基础功能测试完成！
```

---

### flexconnect_mode_switch_demo.py - 交互式模式切换

**功能：** 交互式演示 FlexConnect 产品的模式切换功能。

**运行方法：**
```bash
python examples/FlexConnect/flexconnect_mode_switch_demo.py
```

**使用方法：**
1. 程序启动后会自动连接第一个可用的 FlexConnect 设备
2. 显示当前模式和故障状态
3. 按回车键循环切换模式：PC → UDISK1 → UDISK2 → PC → ...
4. 输入 `q` 退出程序

**现象效果：**
- 实时显示当前模式（PC/UDISK1/UDISK2）
- 显示故障状态（如果有）
- 每次切换后自动验证模式是否正确设置
- 支持优雅退出，退出时恢复设备状态

**适用场景：**
- 快速演示模式切换功能
- 验证设备响应
- 测试模式切换的稳定性
- 学习 FlexConnect API 使用

---

### power_restore_demo.py - 掉电恢复功能演示

**功能：** 完整演示掉电恢复功能，包括优先级测试。

**运行方法：**
```bash
python examples/FlexConnect/power_restore_demo.py
```

**演示内容：**
1. 启用/禁用掉电恢复功能
2. 设置上电默认模式
3. 模拟掉电恢复场景
4. 验证掉电恢复优先级逻辑

**核心知识点：**
- **掉电恢复启用**: 断电重启后恢复到上次的工作模式
- **掉电恢复禁用**: 断电重启后使用上电默认模式
- **优先级**: channel_default_power_flag > poweroff_recover > flexconnect_default_mode

**适用场景：**
- 🎯 需要断电后自动恢复状态
- 🎯 自动化测试环境
- 🎯 无人值守场景
- 🎯 理解掉电恢复逻辑

**应用建议：**
```
开发调试环境: 禁用掉电恢复，固定默认为 PC 模式
自动化测试环境: 启用掉电恢复，保持测试状态
生产环境: 根据实际需求选择合适的配置
```

---

### automation_suite.py - 自动化测试框架

**功能：** 完整的自动化测试套件，包含 ADB 和 U 盘测试。

**运行方法：**
```bash
python examples/FlexConnect/automation_suite.py
```

**测试套件：**
- ✅ ADB 设备连接测试
- ✅ ADB 命令执行测试
- ✅ U 盘访问测试
- ✅ 模式循环切换测试
- ✅ 掉电恢复功能测试

**输出报告：**
测试完成后会生成报告文件：
```
flexconnect_test_report_20250106_143052.txt
```

**前置要求：**
- 安装 Android SDK Platform Tools (包含 adb 命令)
- 车机已连接并开启 USB 调试
- U 盘已插入

**适用场景：**
- 🎯 车机开发自动化测试
- 🎯 CI/CD 集成
- 🎯 夜间回归测试
- 🎯 产品验收测试

---

### diagnose_params.py - 参数诊断工具

**功能：** 读取并显示 FlexConnect 设备的所有相关参数，用于排查掉电恢复逻辑问题。

**运行方法：**
```bash
python examples/FlexConnect/diagnose_params.py
```

**输出信息：**
- 设备基本信息（端口、硬件版本、固件版本）
- 当前 FlexConnect 模式
- 上电默认模式
- 掉电恢复状态（启用/禁用）
- 通道电源状态
- 其他相关参数

**适用场景：**
- 排查掉电恢复逻辑问题
- 调试设备参数设置
- 验证参数持久化
- 检查设备配置状态

---

## 📖 学习路径

推荐按以下顺序学习：

### 🔰 入门阶段
1. **basic_usage.py** - 了解基本连接和控制方法
2. **flexconnect_mode_switch_demo.py** - 练习交互式操作

### 🎓 进阶阶段
3. **power_restore_demo.py** - 掌握掉电恢复和状态管理
4. **diagnose_params.py** - 学会使用诊断工具

### 🚀 高级阶段
5. **automation_suite.py** - 构建自动化测试框架
6. 参考完整测试套件（位于 `test/FlexConnect/`）

---

## 💡 代码模板

### 最简单的连接和切换

```python
from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1

# 连接
hub = SmartUSBHub.scan_and_connect()

# 切换到 PC 模式
hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)

# 切换到 U 盘模式
hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)

# 断开
hub.disconnect()
```

### 使用上下文管理器

```python
from contextlib import contextmanager
from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC

@contextmanager
def flexconnect_device():
    hub = SmartUSBHub.scan_and_connect()
    try:
        yield hub
    finally:
        hub.disconnect()

# 使用
with flexconnect_device() as hub:
    hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
    # ... 其他操作
```

### 错误处理

```python
from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC

hub = SmartUSBHub.scan_and_connect()
if hub is None:
    print("连接失败")
    exit(1)

try:
    result = hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
    if not result:
        print("切换失败")
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
finally:
    hub.disconnect()
```

---

## 🔍 与测试文件的区别

**示例程序（本目录）：**
- `basic_usage.py` - 基础入门教程
- `flexconnect_mode_switch_demo.py` - 交互式演示
- `power_restore_demo.py` - 功能演示
- `automation_suite.py` - 自动化测试框架
- `diagnose_params.py` - 诊断工具

**测试文件（test/FlexConnect/）：**
- `test_integration.py` - 接口集成测试（使用 pytest）
- `test_stress.py` - 压力测试（使用 pytest）
- `test_scenario_*.py` - 各种测试场景脚本
- `flexconnect_advanced_test.py` - 高级功能测试

如需运行完整的测试套件，请参考 `test/FlexConnect/` 目录。

---

## 🔧 常见问题

### Q1: 运行示例时提示 "未找到设备"

**A**: 检查以下事项：
1. 设备是否已连接并上电
2. 驱动是否已安装（Windows 需要 CDC 驱动）
3. 权限是否足够（Linux 需要添加 udev 规则）

**Linux 解决方案**:
```bash
# 添加用户到 dialout 组
sudo usermod -a -G dialout $USER

# 添加 udev 规则
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", MODE="0666"' | \
    sudo tee /etc/udev/rules.d/99-smartusbhub.rules

# 重新加载规则
sudo udevadm control --reload-rules

# 注销重新登录
```

### Q2: ADB 测试失败

**A**: 确保：
1. 已安装 Android SDK Platform Tools
2. adb 在系统 PATH 中：`adb version`
3. 车机已开启 USB 调试
4. 车机 USB 模式设置为 MTP 或 PTP

### Q3: 模式切换后设备未识别

**A**: 增加等待时间：
```python
hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
time.sleep(1.0)  # 等待设备枚举
```

### Q4: 掉电恢复不工作

**A**: 
1. 确认已启用：`hub.set_auto_restore(True)`
2. 切换模式后等待至少 3 秒再断电（Flash 写入延迟）
3. 检查固件版本是否最新

---

## 💡 使用技巧

### 快速测试

1. **基础功能**: 先运行 `basic_usage.py` 验证设备连接
2. **交互测试**: 使用 `flexconnect_mode_switch_demo.py` 快速体验
3. **问题诊断**: 遇到问题时运行 `diagnose_params.py` 查看参数

### 开发调试

1. **复制模板**: 从 `basic_usage.py` 开始修改
2. **参考示例**: 查看其他示例了解高级用法
3. **错误处理**: 参考 `automation_suite.py` 的错误处理机制

---

## ⚠️ 注意事项

1. **设备连接**
   - 确保设备已正确连接并识别
   - 检查串口权限（Linux/macOS 可能需要 sudo）
   - 确保没有其他程序占用设备

2. **功能支持**
   - 需要设备支持 FlexConnect 功能
   - 某些功能需要特定固件版本支持

3. **错误处理**
   - 如果出现 "No Smart USB Hub found"，检查设备连接
   - 如果出现通信错误，检查串口是否被占用
   - 如果模式切换失败，检查设备是否支持该模式

---

## 📚 相关文档

### 产品文档
- **产品规格书**: `products/SmartUSBSwitch_FlexConnect/document/产品规格书_SmartUSBSwitch_FlexConnect.md`
- **API 使用文档**: `products/SmartUSBSwitch_FlexConnect/document/API使用文档_SmartUSBSwitch_FlexConnect.md`
- **快速开始指南**: `products/SmartUSBSwitch_FlexConnect/document/快速开始指南.md`

### 测试文档
- **测试套件**: `test/FlexConnect/` - FlexConnect 完整测试套件
- **测试指南**: `test/FlexConnect/README.md` - 测试使用说明

### 其他示例
- [SmartUSBHub Pro 示例](../SmartUSBHub_Pro/README.md)
- [通用示例](../Common/README.md)

---

## 🔗 快速链接

- [主 README](../../README.md) - 项目总览
- [smartusbhub.py](../../smartusbhub.py) - Python 库源码
- [测试目录](../../test/FlexConnect/) - 完整测试套件

---

**最后更新**: 2025-01-06  
**版本**: 2.0.0

© 2025 makerlabtools. All Rights Reserved.
