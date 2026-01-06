# FlexConnect 测试脚本总览

本文档汇总了所有 FlexConnect 功能验证测试脚本。

## 测试脚本列表

### 📂 测试脚本位置

所有测试脚本位于：
```
SmartUSBHub_Pro-4CH_USB2.0/library/smartusbhub_ng/examples/smartusbswitch_flexconnect/
```

---

## 基础功能测试

### 1. 诊断工具

#### `diagnose_params.py` - 参数诊断工具

**用途**：读取并显示所有相关参数，用于排查问题

**运行**：
```bash
python examples/smartusbswitch_flexconnect/diagnose_params.py
```

**输出**：
- 当前 FlexConnect 模式
- 上电默认模式
- 掉电恢复状态
- 设备信息
- 断电重启预测

---

## 完整测试套件（按验证指南）

### 测试二：掉电恢复功能验证

#### `test_scenario_2_3.py` - 测试场景 2.3

**测试内容**：禁用掉电恢复 - 使用默认模式

**运行**：
```bash
python examples/smartusbswitch_flexconnect/test_scenario_2_3.py
```

**测试步骤**：
1. 设置默认模式为 PC
2. 禁用掉电恢复
3. 切换到 UDISK2 模式
4. 断电重启
5. **验证**：应该恢复到 PC 模式（不是UDISK2）

**关键验证**：
- ✅ 禁用掉电恢复后，不使用保存的模式
- ✅ 使用上电默认模式

---

#### `test_scenario_2_4.py` - 测试场景 2.4

**测试内容**：掉电恢复状态持久化

**运行**：
```bash
python examples/smartusbswitch_flexconnect/test_scenario_2_4.py
```

**测试步骤**：
1. 启用掉电恢复，切换到 UDISK1
2. 多次断电重启（3次），每次验证是否恢复到 UDISK1
3. 切换到 UDISK2，断电重启，验证是否恢复到 UDISK2

**关键验证**：
- ✅ 掉电恢复功能正常工作
- ✅ 参数持久化功能正常工作
- ✅ Flash 读写功能正常工作

**预计时间**：约5-10分钟（需要4次断电重启）

---

### 测试三：优先级逻辑验证（关键测试）

#### `test_scenario_3_priority.py` - 优先级逻辑验证

**测试内容**：验证上电恢复的优先级顺序

**运行**：
```bash
python examples/smartusbswitch_flexconnect/test_scenario_3_priority.py
```

**测试场景**：
- **场景 3.1**：只有上电默认模式（最低优先级）
- **场景 3.2**：掉电恢复 > 上电默认模式
- **场景 3.3**：默认电源标志 > 掉电恢复（说明，需要特殊设置）

**优先级顺序**（从高到低）：
```
1. 默认电源标志 (channel_default_power_flag)     ← 最高优先级
2. 掉电恢复 (poweroff_recover + channel_power_status) ← 中等优先级
3. 上电默认模式 (flexconnect_default_mode)        ← 最低优先级（兜底）
```

**关键验证**：
- ✅ 优先级逻辑正确
- ✅ 恢复逻辑按照正确的顺序执行
- ✅ 每个优先级都能正确工作

**预计时间**：约10-15分钟（需要2次断电重启）

---

### 测试四：恢复出厂设置验证

#### `test_scenario_4_factory_reset.py` - 恢复出厂设置

**测试内容**：验证恢复出厂设置功能

**运行**：
```bash
python examples/smartusbswitch_flexconnect/test_scenario_4_factory_reset.py
```

**测试场景**：
- **场景 4.1**：恢复出厂设置功能（协议命令）
- **场景 4.2**：恢复出厂设置后断电重启
- **场景 4.3**：按键长按恢复出厂设置（手动测试）

**验证的默认值**：
- `flexconnect_default_mode` → `MODE_PC (0)`
- `poweroff_recover` → `0` (禁用)
- `channel_power_status` → 全部清零
- 当前模式 → `MODE_PC`

**关键验证**：
- ✅ 协议命令恢复出厂设置功能正常
- ✅ 参数持久化功能正常
- ✅ 按键恢复出厂设置功能正常
- ✅ 所有参数都能正确恢复为出厂默认值

**预计时间**：约10分钟（需要1次断电重启 + 可选的按键测试）

---

### 测试五：按键功能与掉电保存联动

#### `test_scenario_5_button_poweroff.py` - 按键与掉电保存联动

**测试内容**：验证按键切换与掉电恢复的联动逻辑

**运行**：
```bash
python examples/smartusbswitch_flexconnect/test_scenario_5_button_poweroff.py
```

**测试场景**：
- **场景 5.1**：启用掉电恢复 + 按键切换
- **场景 5.2**：禁用掉电恢复 + 按键切换

**按键功能**：
- 按键1（短按）：切换到 PC 模式
- 按键2（短按）：切换到 UDISK1 模式
- 按键3（短按）：切换到 UDISK2 模式

**关键验证**：
- ✅ 启用掉电恢复时，按键切换的模式被正确保存
- ✅ 禁用掉电恢复时，按键切换的模式不会被保存
- ✅ 按键功能与掉电保存联动逻辑正确

**预计时间**：约10-15分钟（需要2次断电重启 + 物理按键操作）

**⚠️ 注意**：此测试需要物理操作硬件按键

---

### 测试六：边界条件和异常测试

#### `test_scenario_6_boundary.py` - 边界条件和异常测试

**测试内容**：验证系统在各种边界条件和异常情况下的行为

**运行**：
```bash
python examples/smartusbswitch_flexconnect/test_scenario_6_boundary.py
```

**测试场景**：
- **场景 6.1**：无效参数测试
- **场景 6.2**：快速连续模式切换（10次）
- **场景 6.3**：重复设置相同值
- **场景 6.4**：多次断电重启持久化验证（5次重启）
- **场景 6.5**：参数读取一致性验证

**测试内容详解**：
- **无效参数**：超出范围的模式值、负数、DISCONNECT作为默认模式等
- **快速切换**：验证在短时间内连续切换模式的稳定性
- **重复设置**：验证设备对重复设置相同值的处理能力
- **多次重启**：验证 Flash 持久化在多次重启后的可靠性
- **读取一致性**：验证多次读取参数是否返回一致结果

**关键验证**：
- ✅ 输入验证逻辑完善，能正确拒绝无效参数
- ✅ 快速连续切换稳定可靠
- ✅ 重复操作处理正常，不产生异常
- ✅ Flash 持久化可靠，多次重启后参数不变
- ✅ 参数读取一致性良好

**预计时间**：约15-30分钟（场景 6.4 可选，需要5次断电重启）

**⚠️ 注意**：场景 6.4 需要多次断电重启，可以选择跳过

---

## 其他测试工具

### `flexconnect_test_default_set.py` - 默认模式设置测试

**用途**：测试设置和读取上电默认模式

**运行**：
```bash
python examples/smartusbswitch_flexconnect/flexconnect_test_default_set.py
```

**测试内容**：
- 设置默认模式为 UDISK1 并验证
- 设置默认模式为 PC 并验证

---

### `flexconnect_test_power_recover.py` - 掉电恢复简单测试

**用途**：简单的掉电恢复测试

**运行**：
```bash
python examples/smartusbswitch_flexconnect/flexconnect_test_power_recover.py
```

---

### `flexconnect_mode_switch_demo.py` - 模式切换演示

**用途**：演示 FlexConnect 模式切换功能

**运行**：
```bash
python examples/smartusbswitch_flexconnect/flexconnect_mode_switch_demo.py
```

**功能**：
- 自动扫描并连接 FlexConnect 设备
- 循环切换模式：PC → UDISK1 → UDISK2 → DISCONNECT → PC
- 显示当前模式和故障状态
- 支持手动控制（按回车切换，输入 'q' 退出）

---

## 完整测试流程

### 推荐测试顺序

1. **诊断当前状态**
   ```bash
   python examples/smartusbswitch_flexconnect/diagnose_params.py
   ```

2. **测试场景 2.3** - 禁用掉电恢复
   ```bash
   python examples/smartusbswitch_flexconnect/test_scenario_2_3.py
   ```

3. **测试场景 2.4** - 掉电恢复持久化
   ```bash
   python examples/smartusbswitch_flexconnect/test_scenario_2_4.py
   ```

4. **测试三** - 优先级逻辑（关键）
   ```bash
   python examples/smartusbswitch_flexconnect/test_scenario_3_priority.py
   ```

5. **测试四** - 恢复出厂设置
   ```bash
   python examples/smartusbswitch_flexconnect/test_scenario_4_factory_reset.py
   ```

6. **测试五** - 按键与掉电保存联动
   ```bash
   python examples/smartusbswitch_flexconnect/test_scenario_5_button_poweroff.py
   ```

7. **测试六** - 边界条件和异常测试
   ```bash
   python examples/smartusbswitch_flexconnect/test_scenario_6_boundary.py
   ```

### 快速验证（最小测试集）

如果时间有限，至少运行这些测试：

```bash
# 1. 禁用掉电恢复测试（关键BUG验证）
python examples/smartusbswitch_flexconnect/test_scenario_2_3.py

# 2. 优先级逻辑测试（关键逻辑验证）
python examples/smartusbswitch_flexconnect/test_scenario_3_priority.py

# 3. 恢复出厂设置测试（基础功能验证）
python examples/smartusbswitch_flexconnect/test_scenario_4_factory_reset.py

# 4. 边界条件测试（场景 6.1, 6.2, 6.3, 6.5，跳过 6.4）
python examples/smartusbswitch_flexconnect/test_scenario_6_boundary.py
```

**预计时间**：约30分钟

---

## 测试前准备

### 硬件准备
- ✅ FlexConnect 硬件设备 × 1
- ✅ USB 转串口线（或 USB 连接）
- ✅ 可控电源开关（用于断电重启）
- ✅ PC 或 UDISK 用于验证连接（可选）

### 软件准备
```bash
cd SmartUSBHub_Pro-4CH_USB2.0/library/smartusbhub_ng
pip install -r requirements.txt
```

### 固件准备
确保固件已经应用了以下修复：
- ✅ 禁用掉电恢复时清除 `channel_power_status`
- ✅ 按键2长按禁用掉电恢复时清除状态
- ✅ 恢复逻辑优先级正确

---

## 预期测试结果

### 全部通过的标志

如果所有测试都通过，你应该看到：

```
测试场景 2.3: ✓ 通过
测试场景 2.4: ✓ 通过
测试场景 3.1: ✓ 通过
测试场景 3.2: ✓ 通过
测试场景 3.3: ⊘ 跳过（需要特殊设置）
测试场景 4.1: ✓ 通过
测试场景 4.2: ✓ 通过
测试场景 4.3: ✓ 通过（如果进行了手动测试）
测试场景 5.1: ✓ 通过
测试场景 5.2: ✓ 通过
测试场景 6.1: ✓ 通过
测试场景 6.2: ✓ 通过
测试场景 6.3: ✓ 通过
测试场景 6.4: ✓ 通过（如果进行了测试）或 ⊘ 跳过
测试场景 6.5: ✓ 通过
```

### 结论

✅ **掉电恢复功能正常工作**
- 启用时正确保存和恢复状态
- 禁用时使用默认模式

✅ **优先级逻辑正确**
- 默认电源标志 > 掉电恢复 > 上电默认模式

✅ **恢复出厂设置功能正常**
- 所有参数正确恢复为默认值
- 参数持久化正常工作

✅ **Flash 读写功能正常**
- 参数能正确保存到 Flash
- 断电重启后能正确读取

✅ **按键功能与掉电保存联动正确**
- 按键切换在启用掉电恢复时被保存
- 按键切换在禁用掉电恢复时不被保存

✅ **边界条件处理完善**
- 正确拒绝无效参数
- 快速连续切换稳定可靠
- 重复操作处理正常
- 参数读取一致性良好

---

## 故障排查

### 如果测试失败

#### 场景 2.3 失败（禁用掉电恢复后仍恢复到保存的模式）
- **原因**：`channel_power_status` 没有被清除
- **检查**：固件是否应用了清除逻辑修复
- **文件**：`smart_switch_protocol.c`, `smart_switch_gpio.c`

#### 场景 2.4 失败（多次重启后模式不一致）
- **原因**：Flash 读写有问题或延迟保存未触发
- **检查**：
  - Flash 写入函数是否正常
  - 延迟保存循环是否正常工作
  - 是否有时序问题

#### 场景 3.1/3.2 失败（优先级错误）
- **原因**：恢复逻辑的优先级顺序不正确
- **检查**：`smart_switch_params.c:smart_switch_status_recover()`
- **验证**：`mode_found` 标志逻辑是否正确

#### 场景 4.1/4.2 失败（恢复出厂设置不完整）
- **原因**：`smart_switch_params_reset()` 没有重置所有参数
- **检查**：
  - `flexconnect_default_mode` 是否设置为 `MODE_PC`
  - `poweroff_recover` 是否设置为 `0`
  - `channel_power_status` 是否清零

#### 场景 5.1 失败（按键切换未保存）
- **原因**：按键切换时未写入 Flash
- **检查**：`smart_switch_gpio.c` 按键处理逻辑
- **验证**：
  - 按键切换时是否检查了 `poweroff_recover`
  - 是否调用了 `smart_switch_params_write()`

#### 场景 5.2 失败（禁用掉电恢复后按键切换仍被保存）
- **原因**：按键切换未检查 `poweroff_recover` 标志
- **检查**：`smart_switch_gpio.c` 按键处理逻辑
- **修复**：只在 `poweroff_recover` 启用时保存状态

#### 场景 6.1 失败（接受了无效参数）
- **原因**：输入验证不完整
- **检查**：
  - Python 库的参数验证
  - 固件的参数范围检查

#### 场景 6.2 失败（快速切换不稳定）
- **原因**：状态机处理不当或延迟不足
- **检查**：
  - 模式切换逻辑是否有竞态条件
  - 协议通信是否可靠

#### 场景 6.4 失败（多次重启后参数丢失）
- **原因**：Flash 磨损或写入失败
- **检查**：
  - Flash 写入次数是否过多
  - Flash 区域是否有坏块
  - checksum 验证是否正确

#### 场景 6.5 失败（参数读取不一致）
- **原因**：协议通信不稳定或缓存问题
- **检查**：
  - 协议响应是否正确
  - 是否有缓存同步问题

---

## 文档索引

- **验证指南**：`VALIDATION_GUIDE.md` - 完整的手动验证步骤
- **硬件测试指南**：`HARDWARE_TEST_GUIDE.md` - 硬件到货后的测试指南
- **BUG 修复文档**：`BUG_FIX_POWEROFF_RECOVER.md` - 掉电恢复逻辑 BUG 修复说明
- **协议方法分类**：`PROTOCOL_METHODS_CLASSIFICATION.md` - 协议方法分类文档

---

## 联系与反馈

如果遇到问题或需要帮助，请：
1. 先运行诊断工具：`diagnose_params.py`
2. 检查固件版本是否正确
3. 查看相关文档中的故障排查部分
4. 记录详细的错误信息和测试环境

---

**最后更新**：2025-01-06
**文档版本**：v1.0

