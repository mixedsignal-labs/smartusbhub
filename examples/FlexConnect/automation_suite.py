"""
Demo 03: 车机自动化测试演示

演示内容：
1. 自动化测试框架
2. ADB 命令自动化
3. U 盘文件验证
4. 测试报告生成

适用场景：
- 车机开发自动化测试
- CI/CD 集成
- 夜间回归测试
"""

import sys
import time
import subprocess
import os
from datetime import datetime

from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1


class FlexConnectAutomationTester:
    """FlexConnect 自动化测试器"""
    
    def __init__(self):
        self.hub = None
        self.test_results = []
        self.start_time = None
        
    def connect(self):
        """连接设备"""
        print("正在连接 FlexConnect 设备...")
        self.hub = SmartUSBHub.scan_and_connect()
        
        if self.hub is None:
            print("✗ 连接失败")
            return False
        
        info = self.hub.get_device_info()
        print(f"✓ 已连接: {info['product_name']}")
        print(f"  固件版本: {info['firmware_version']}")
        print(f"  序列号: {info['serial_number']}")
        
        return True
    
    def disconnect(self):
        """断开连接"""
        if self.hub:
            self.hub.disconnect()
            self.hub = None
    
    def switch_to_mode(self, mode, mode_name):
        """切换到指定模式并验证"""
        print(f"\n→ 切换到 {mode_name}...")
        
        result = self.hub.set_flexconnect_mode(mode)
        if not result:
            print(f"✗ 切换失败")
            return False
        
        time.sleep(0.5)
        
        current_mode = self.hub.get_flexconnect_mode()
        if current_mode != mode:
            print(f"✗ 验证失败: 期望 {mode}, 实际 {current_mode}")
            return False
        
        print(f"✓ 成功切换到 {mode_name}")
        return True
    
    def run_test(self, test_name, test_func):
        """运行单个测试"""
        print("\n" + "=" * 60)
        print(f"[测试] {test_name}")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            result = test_func()
            elapsed_time = time.time() - start_time
            
            if result:
                print(f"\n✓ {test_name} - 通过 ({elapsed_time:.2f}秒)")
            else:
                print(f"\n✗ {test_name} - 失败 ({elapsed_time:.2f}秒)")
            
            self.test_results.append({
                'name': test_name,
                'result': result,
                'time': elapsed_time
            })
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"\n✗ {test_name} - 异常: {e} ({elapsed_time:.2f}秒)")
            
            self.test_results.append({
                'name': test_name,
                'result': False,
                'time': elapsed_time,
                'error': str(e)
            })
            
            return False
    
    def test_adb_connection(self):
        """测试 ADB 连接"""
        print("\n[步骤1] 切换到 PC 模式...")
        if not self.switch_to_mode(FLEXCONNECT_MODE_PC, "PC 模式"):
            return False
        
        print("\n[步骤2] 等待 ADB 设备枚举...")
        time.sleep(3)  # 等待设备枚举
        
        print("\n[步骤3] 检查 ADB 设备...")
        try:
            # 执行 adb devices
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"ADB 输出:\n{result.stdout}")
            
            # 检查是否有设备
            if 'device' in result.stdout and 'List of devices' in result.stdout:
                lines = result.stdout.strip().split('\n')
                # 过滤掉标题行和空行
                devices = [line for line in lines[1:] if line.strip() and '\tdevice' in line]
                
                if devices:
                    print(f"✓ 找到 {len(devices)} 个 ADB 设备")
                    return True
                else:
                    print("✗ 未找到 ADB 设备")
                    return False
            else:
                print("✗ ADB 未识别到设备")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ ADB 命令超时")
            return False
        except FileNotFoundError:
            print("✗ ADB 未安装或不在 PATH 中")
            print("  提示: 请安装 Android SDK Platform Tools")
            return False
        except Exception as e:
            print(f"✗ ADB 测试失败: {e}")
            return False
    
    def test_adb_commands(self):
        """测试 ADB 命令执行"""
        print("\n[步骤1] 切换到 PC 模式...")
        if not self.switch_to_mode(FLEXCONNECT_MODE_PC, "PC 模式"):
            return False
        
        time.sleep(3)
        
        print("\n[步骤2] 执行 ADB 命令...")
        commands = [
            ('adb shell getprop ro.product.model', '获取产品型号'),
            ('adb shell getprop ro.build.version.release', '获取系统版本'),
            ('adb shell uptime', '获取运行时间'),
        ]
        
        for cmd, desc in commands:
            print(f"\n  → {desc}: {cmd}")
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    print(f"    ✓ {output}")
                else:
                    print(f"    ✗ 命令失败: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"    ✗ 执行失败: {e}")
                return False
        
        print("\n✓ 所有 ADB 命令执行成功")
        return True
    
    def test_udisk_access(self):
        """测试 U 盘访问"""
        print("\n[步骤1] 切换到 U 盘模式...")
        if not self.switch_to_mode(FLEXCONNECT_MODE_UDISK1, "U 盘模式"):
            return False
        
        print("\n[步骤2] 等待 U 盘挂载...")
        time.sleep(3)
        
        print("\n[步骤3] 验证 U 盘访问...")
        print("  注意: 此测试需要车机端配合验证")
        print("  建议手动检查车机是否能识别 U 盘")
        
        # 这里可以添加具体的验证逻辑
        # 例如：检查车机日志、查询车机状态等
        
        print("\n✓ U 盘模式切换成功（需要手动验证车机识别）")
        return True
    
    def test_mode_cycling(self):
        """测试模式循环切换"""
        print("\n[步骤1] 循环切换模式（10次）...")
        
        modes = [
            (FLEXCONNECT_MODE_PC, "PC"),
            (FLEXCONNECT_MODE_UDISK1, "UDISK1"),
        ]
        
        for i in range(10):
            print(f"\n  第 {i+1}/10 轮:")
            for mode, name in modes:
                if not self.switch_to_mode(mode, name):
                    print(f"✗ 第 {i+1} 轮切换失败")
                    return False
                time.sleep(0.3)
        
        print("\n✓ 10 轮循环切换完成")
        return True
    
    def test_auto_restore(self):
        """测试掉电恢复"""
        print("\n[步骤1] 启用掉电恢复...")
        result = self.hub.set_auto_restore(True)
        if not result:
            print("✗ 启用失败")
            return False
        
        time.sleep(0.2)
        
        status = self.hub.get_auto_restore_status()
        if status != 1:
            print("✗ 验证失败")
            return False
        
        print("✓ 掉电恢复已启用")
        
        print("\n[步骤2] 切换到 UDISK1 模式...")
        if not self.switch_to_mode(FLEXCONNECT_MODE_UDISK1, "U 盘模式"):
            return False
        
        print("\n说明: 现在断电重启后，设备会自动恢复到 U 盘模式")
        print("      (需要手动断电验证)")
        
        return True
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['result'])
        failed = total - passed
        total_time = sum(r['time'] for r in self.test_results)
        
        print(f"\n总计: {total} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"总耗时: {total_time:.2f} 秒")
        
        print("\n详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status = "✓" if result['result'] else "✗"
            print(f"  {status} {i}. {result['name']} - {result['time']:.2f}秒")
            if 'error' in result:
                print(f"      错误: {result['error']}")
        
        print("\n" + "=" * 60)
        
        # 保存到文件
        report_file = f"flexconnect_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("FlexConnect 自动化测试报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总计: {total} 个测试\n")
                f.write(f"通过: {passed} 个\n")
                f.write(f"失败: {failed} 个\n")
                f.write(f"总耗时: {total_time:.2f} 秒\n")
                f.write("\n详细结果:\n")
                for i, result in enumerate(self.test_results, 1):
                    status = "✓" if result['result'] else "✗"
                    f.write(f"  {status} {i}. {result['name']} - {result['time']:.2f}秒\n")
                    if 'error' in result:
                        f.write(f"      错误: {result['error']}\n")
            
            print(f"\n报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n警告: 无法保存报告文件: {e}")


def main():
    print("=" * 60)
    print("FlexConnect 车机自动化测试演示")
    print("=" * 60)
    
    tester = FlexConnectAutomationTester()
    tester.start_time = time.time()
    
    # 连接设备
    if not tester.connect():
        return 1
    
    try:
        # 运行测试套件
        print("\n开始运行测试套件...")
        
        # 测试1: ADB 连接
        tester.run_test(
            "ADB 设备连接测试",
            tester.test_adb_connection
        )
        
        # 测试2: ADB 命令
        tester.run_test(
            "ADB 命令执行测试",
            tester.test_adb_commands
        )
        
        # 测试3: U 盘访问
        tester.run_test(
            "U 盘访问测试",
            tester.test_udisk_access
        )
        
        # 测试4: 模式循环
        tester.run_test(
            "模式循环切换测试",
            tester.test_mode_cycling
        )
        
        # 测试5: 掉电恢复
        tester.run_test(
            "掉电恢复功能测试",
            tester.test_auto_restore
        )
        
        # 生成报告
        tester.generate_report()
        
        # 恢复默认状态
        print("\n[清理] 恢复默认状态...")
        tester.hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)
        print("✓ 已恢复到 PC 模式")
        
    except KeyboardInterrupt:
        print("\n\n用户中断测试 (Ctrl+C)")
        return 1
    
    finally:
        tester.disconnect()
        print("\n已断开连接")
    
    # 检查测试结果
    passed = sum(1 for r in tester.test_results if r['result'])
    total = len(tester.test_results)
    
    if passed == total:
        print("\n✓✓✓ 所有测试通过！✓✓✓")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

