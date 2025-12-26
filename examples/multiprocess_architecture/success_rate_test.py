"""
成功率测试程序
基于 business_process 架构，统计操作的成功与失败率
"""
import sys
import os
import time
import signal
import threading
from multiprocessing import Process, Manager, Queue
from collections import defaultdict
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
# 导入当前目录的模块
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_server import server_process_main
from smartusbhub_client import SmartUSBHubClient


class TestStats:
    """测试统计信息（使用 Manager 创建的共享对象）"""
    
    def __init__(self, manager):
        """初始化统计对象"""
        # 注意：不保存 manager 引用，因为它不能被 pickle
        self.total_operations = manager.Value('i', 0)
        self.successful_operations = manager.Value('i', 0)
        self.failed_operations = manager.Value('i', 0)
        
        # 按操作类型统计 - 预先初始化所有可能的操作
        self.operation_stats = manager.dict()
        # 预先创建所有操作的统计字典
        operations = ['set_channel_power', 'get_channel_power_status', 
                     'get_channel_voltage', 'get_channel_current']
        for op in operations:
            self.operation_stats[op] = manager.dict({
                'total': 0,
                'success': 0,
                'fail': 0
            })
        
        # 按通道统计 - 预先初始化所有通道（支持1-4通道）
        self.channel_stats = manager.dict()
        for ch in [1, 2, 3, 4]:
            self.channel_stats[ch] = manager.dict({
                'total': 0,
                'success': 0,
                'fail': 0
            })
        
        # 错误类型统计
        self.error_types = manager.dict()
        
        self.lock = manager.Lock()
        
    def _get_operation_stats(self, operation):
        """获取操作统计，如果不存在则创建"""
        if operation not in self.operation_stats:
            # 如果操作不存在，需要创建，但这需要 manager
            # 为了避免这个问题，我们在初始化时预先创建所有操作
            # 如果确实需要动态创建，可以使用 Manager() 但这不是最佳实践
            # 这里我们假设所有操作都已预先创建
            pass
        return self.operation_stats.get(operation, None)
    
    def _get_channel_stats(self, channel):
        """获取通道统计，如果不存在则创建"""
        if channel not in self.channel_stats:
            # 如果通道不存在，需要创建，但这需要 manager
            # 为了避免这个问题，我们在初始化时预先创建所有通道
            # 如果确实需要动态创建，可以使用 Manager() 但这不是最佳实践
            # 这里我们假设所有通道都已预先创建
            pass
        return self.channel_stats.get(channel, None)
    
    def record_success(self, operation, channel=None):
        """记录成功操作"""
        with self.lock:
            self.total_operations.value += 1
            self.successful_operations.value += 1
            
            op_stats = self._get_operation_stats(operation)
            if op_stats is not None:
                op_stats['total'] += 1
                op_stats['success'] += 1
            else:
                # 如果操作不存在，动态创建（需要 manager，但这里我们无法访问）
                # 为了简化，我们跳过这个操作的统计
                pass
            
            if channel:
                ch_stats = self._get_channel_stats(channel)
                if ch_stats is not None:
                    ch_stats['total'] += 1
                    ch_stats['success'] += 1
    
    def record_failure(self, operation, error_type="unknown", channel=None, error_msg=""):
        """记录失败操作"""
        with self.lock:
            self.total_operations.value += 1
            self.failed_operations.value += 1
            
            op_stats = self._get_operation_stats(operation)
            if op_stats is not None:
                op_stats['total'] += 1
                op_stats['fail'] += 1
            
            # 统计错误类型
            if error_type not in self.error_types:
                self.error_types[error_type] = 0
            self.error_types[error_type] += 1
            
            if channel:
                ch_stats = self._get_channel_stats(channel)
                if ch_stats is not None:
                    ch_stats['total'] += 1
                    ch_stats['fail'] += 1
    
    def get_summary(self):
        """获取统计摘要"""
        with self.lock:
            total = self.total_operations.value
            success = self.successful_operations.value
            fail = self.failed_operations.value
            
            success_rate = (success / total * 100) if total > 0 else 0
            fail_rate = (fail / total * 100) if total > 0 else 0
            
            # 转换操作统计
            op_stats = {}
            for op, stats in self.operation_stats.items():
                op_total = stats.get('total', 0)
                op_success = stats.get('success', 0)
                op_fail = stats.get('fail', 0)
                op_success_rate = (op_success / op_total * 100) if op_total > 0 else 0
                op_stats[op] = {
                    'total': op_total,
                    'success': op_success,
                    'fail': op_fail,
                    'success_rate': op_success_rate
                }
            
            # 转换通道统计
            ch_stats = {}
            for ch, stats in self.channel_stats.items():
                ch_total = stats.get('total', 0)
                ch_success = stats.get('success', 0)
                ch_fail = stats.get('fail', 0)
                ch_success_rate = (ch_success / ch_total * 100) if ch_total > 0 else 0
                ch_stats[ch] = {
                    'total': ch_total,
                    'success': ch_success,
                    'fail': ch_fail,
                    'success_rate': ch_success_rate
                }
            
            # 转换错误类型统计
            error_stats = {}
            for err_type, count in self.error_types.items():
                error_stats[err_type] = count
            
            return {
                'total_operations': total,
                'successful_operations': success,
                'failed_operations': fail,
                'success_rate': success_rate,
                'fail_rate': fail_rate,
                'operation_stats': op_stats,
                'channel_stats': ch_stats,
                'error_types': error_stats
            }


def test_business_process(channel, request_queue, response_dict, 
                         total_ops, success_ops, fail_ops,
                         operation_stats, channel_stats, error_types, stats_lock,
                         sleep_after_on, sleep_after_off, max_iterations=None):
    """
    测试业务进程 - 带统计功能
    
    Args:
        channel: 通道编号
        request_queue: 请求队列
        response_dict: 响应字典
        total_ops: 总操作数共享值
        success_ops: 成功操作数共享值
        fail_ops: 失败操作数共享值
        operation_stats: 操作统计共享字典
        channel_stats: 通道统计共享字典
        error_types: 错误类型统计共享字典
        stats_lock: 统计锁
        sleep_after_on: 开启后等待时间
        sleep_after_off: 关闭后等待时间
        max_iterations: 最大迭代次数，None表示无限循环
    """
    process_name = f"TestProcess-{channel}"
    
    print(f"[{process_name}] 测试进程启动，控制通道 {channel}")
    
    # 创建客户端代理
    client = SmartUSBHubClient(request_queue, response_dict)
    
    iteration = 0
    
    def record_success(operation, ch=None):
        """记录成功操作"""
        with stats_lock:
            total_ops.value += 1
            success_ops.value += 1
            if operation in operation_stats:
                operation_stats[operation]['total'] += 1
                operation_stats[operation]['success'] += 1
            if ch and ch in channel_stats:
                channel_stats[ch]['total'] += 1
                channel_stats[ch]['success'] += 1
    
    def record_failure(operation, error_type="unknown", ch=None, error_msg=""):
        """记录失败操作"""
        with stats_lock:
            total_ops.value += 1
            fail_ops.value += 1
            if operation in operation_stats:
                operation_stats[operation]['total'] += 1
                operation_stats[operation]['fail'] += 1
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
            if ch and ch in channel_stats:
                channel_stats[ch]['total'] += 1
                channel_stats[ch]['fail'] += 1
    
    try:
        while True:
            if max_iterations and iteration >= max_iterations:
                print(f"[{process_name}] 达到最大迭代次数 {max_iterations}，退出")
                break
                
            iteration += 1
            
            # ===== 开启电源操作 =====
            try:
                success = client.set_channel_power(channel, state=1)
                if success:
                    record_success('set_channel_power', channel)
                else:
                    record_failure('set_channel_power', 'operation_failed', channel, "操作返回False")
            except TimeoutError as e:
                record_failure('set_channel_power', 'timeout', channel, str(e))
            except Exception as e:
                record_failure('set_channel_power', 'exception', channel, str(e))
            
            # ===== 获取电源状态 =====
            try:
                status = client.get_channel_power_status(channel)
                if status is not None:
                    record_success('get_channel_power_status', channel)
                else:
                    record_failure('get_channel_power_status', 'timeout', channel, "返回None")
            except TimeoutError as e:
                record_failure('get_channel_power_status', 'timeout', channel, str(e))
            except Exception as e:
                record_failure('get_channel_power_status', 'exception', channel, str(e))
            
            # ===== 获取电压 =====
            try:
                voltage = client.get_channel_voltage(channel)
                if voltage is not None:
                    record_success('get_channel_voltage', channel)
                else:
                    record_failure('get_channel_voltage', 'timeout', channel, "返回None")
            except TimeoutError as e:
                record_failure('get_channel_voltage', 'timeout', channel, str(e))
            except Exception as e:
                record_failure('get_channel_voltage', 'exception', channel, str(e))
            
            # ===== 获取电流 =====
            try:
                current = client.get_channel_current(channel)
                if current is not None:
                    record_success('get_channel_current', channel)
                else:
                    record_failure('get_channel_current', 'timeout', channel, "返回None")
            except TimeoutError as e:
                record_failure('get_channel_current', 'timeout', channel, str(e))
            except Exception as e:
                record_failure('get_channel_current', 'exception', channel, str(e))
            
            time.sleep(sleep_after_on)
            
            # ===== 关闭电源操作 =====
            try:
                success = client.set_channel_power(channel, state=0)
                if success:
                    record_success('set_channel_power', channel)
                else:
                    record_failure('set_channel_power', 'operation_failed', channel, "操作返回False")
            except TimeoutError as e:
                record_failure('set_channel_power', 'timeout', channel, str(e))
            except Exception as e:
                record_failure('set_channel_power', 'exception', channel, str(e))
            
            # ===== 获取电源状态 =====
            try:
                status = client.get_channel_power_status(channel)
                if status is not None:
                    record_success('get_channel_power_status', channel)
                else:
                    record_failure('get_channel_power_status', 'timeout', channel, "返回None")
            except TimeoutError as e:
                record_failure('get_channel_power_status', 'timeout', channel, str(e))
            except Exception as e:
                record_failure('get_channel_power_status', 'exception', channel, str(e))
            
            time.sleep(sleep_after_off)
            
    except KeyboardInterrupt:
        print(f"\n[{process_name}] 收到中断信号，正在退出...")
    except Exception as e:
        print(f"[{process_name}] 测试进程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[{process_name}] 测试进程已退出，共执行 {iteration} 次迭代")


class TestManager:
    """测试管理器"""
    
    def __init__(self):
        self.processes = []
        self.running = True
        self.stats = None
        self.start_time = None
        
    def signal_handler(self, sig, frame):
        """信号处理函数"""
        print("\n收到中断信号，正在停止测试...")
        self.running = False
        self.stop_all()
        
    def stop_all(self):
        """停止所有进程"""
        print("[TestManager] 正在停止所有进程...")
        for process in self.processes:
            if process.is_alive():
                print(f"[TestManager] 终止进程: {process.name}")
                process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    print(f"[TestManager] 强制终止进程: {process.name}")
                    process.kill()
                    process.join()
        print("[TestManager] 所有进程已停止")
        
    def run_test(self, channels=[1, 2, 3, 4], sleep_after_on=0.01, sleep_after_off=0.01, 
                 duration=None, max_iterations=None, report_interval=10):
        """
        运行测试
        
        Args:
            channels: 要测试的通道列表
            sleep_after_on: 开启后等待时间（秒）
            sleep_after_off: 关闭后等待时间（秒）
            duration: 测试持续时间（秒），None表示无限运行
            max_iterations: 每个进程的最大迭代次数，None表示无限
            report_interval: 统计报告间隔（秒）
        """
        print("=" * 80)
        print("SmartUSBHub 成功率测试程序")
        print("=" * 80)
        print(f"测试通道: {channels}")
        print(f"执行间隔: 开启后 {sleep_after_on}秒, 关闭后 {sleep_after_off}秒")
        if duration:
            print(f"测试时长: {duration}秒")
        if max_iterations:
            print(f"最大迭代次数: {max_iterations}次/通道")
        print("=" * 80)
        
        # 创建共享资源
        shared_manager = Manager()
        request_queue = Queue()
        response_dict = shared_manager.dict()
        
        # 创建统计对象
        self.stats = TestStats(shared_manager)
        
        # 确保所有测试通道的统计都已创建
        for ch in channels:
            if ch not in self.stats.channel_stats:
                self.stats.channel_stats[ch] = shared_manager.dict({
                    'total': 0,
                    'success': 0,
                    'fail': 0
                })
        
        # 启动服务进程
        print("\n[Test] 启动SmartUSBHub服务进程...")
        server_process = Process(
            target=server_process_main,
            args=(request_queue, response_dict, None),
            name="SmartUSBHub-Server"
        )
        server_process.daemon = False
        server_process.start()
        self.processes.append(server_process)
        
        # 等待服务进程初始化
        print("[Test] 等待服务进程初始化...")
        time.sleep(3)
        
        if not server_process.is_alive():
            print("[Test] 错误: 服务进程启动失败")
            return
            
        print("[Test] 服务进程已启动")
        
        # 启动测试进程
        print(f"\n[Test] 启动 {len(channels)} 个测试进程...")
        test_processes = []
        
        for channel in channels:
            test_process = Process(
                target=test_business_process,
                args=(channel, request_queue, response_dict,
                      self.stats.total_operations,
                      self.stats.successful_operations,
                      self.stats.failed_operations,
                      self.stats.operation_stats,
                      self.stats.channel_stats,
                      self.stats.error_types,
                      self.stats.lock,
                      sleep_after_on, sleep_after_off, max_iterations),
                name=f"TestProcess-{channel}"
            )
            test_process.daemon = False
            test_process.start()
            test_processes.append(test_process)
            self.processes.append(test_process)
            print(f"[Test] TestProcess-{channel} 已启动")
            time.sleep(0.2)  # 错开启动时间
        
        print("\n[Test] 所有测试进程已启动，开始测试...")
        if duration:
            print(f"[Test] 测试将持续 {duration} 秒，按 Ctrl+C 可提前停止")
        else:
            print("[Test] 测试将持续运行，按 Ctrl+C 停止\n")
        
        # 启动统计报告线程
        self.start_time = time.time()
        report_thread = threading.Thread(
            target=self._report_stats, 
            args=(duration, report_interval), 
            daemon=True
        )
        report_thread.start()
        
        try:
            # 等待测试完成或超时
            if duration:
                while time.time() - self.start_time < duration and self.running:
                    time.sleep(1)
                    
                    # 检查服务进程
                    if not server_process.is_alive():
                        print("[Test] 警告: 服务进程已退出")
                        break
                        
                    # 检查测试进程
                    dead_processes = [p for p in test_processes if not p.is_alive()]
                    if dead_processes:
                        for p in dead_processes:
                            print(f"[Test] 警告: {p.name} 已退出")
            else:
                # 无限运行
                while self.running:
                    time.sleep(1)
                    
                    # 检查服务进程
                    if not server_process.is_alive():
                        print("[Test] 警告: 服务进程已退出")
                        break
                        
                    # 检查测试进程
                    dead_processes = [p for p in test_processes if not p.is_alive()]
                    if dead_processes:
                        for p in dead_processes:
                            print(f"[Test] 警告: {p.name} 已退出")
                            
        except KeyboardInterrupt:
            print("\n[Test] 收到中断信号")
        finally:
            # 停止所有进程
            print("\n[Test] 停止所有进程...")
            self.stop_all()
            
            # 打印最终报告
            self._print_final_report()
            
    def _report_stats(self, duration, interval):
        """定期报告统计信息"""
        start_time = time.time()
        
        while self.running:
            if duration and time.time() - start_time >= duration:
                break
                
            time.sleep(interval)
            
            if not self.running:
                break
                
            elapsed = time.time() - start_time
            summary = self.stats.get_summary()
            
            print(f"\n{'='*80}")
            print(f"[实时统计] 已运行 {elapsed:.1f}秒")
            print(f"{'='*80}")
            print(f"总操作数: {summary['total_operations']}")
            print(f"成功: {summary['successful_operations']} | 失败: {summary['failed_operations']}")
            if summary['total_operations'] > 0:
                print(f"成功率: {summary['success_rate']:.2f}% | 失败率: {summary['fail_rate']:.2f}%")
            
            print(f"\n按操作类型统计:")
            for op, stats in sorted(summary['operation_stats'].items()):
                print(f"  {op}:")
                print(f"    总数: {stats['total']} | 成功: {stats['success']} | 失败: {stats['fail']} | 成功率: {stats['success_rate']:.2f}%")
            
            print(f"\n按通道统计:")
            for ch in sorted(summary['channel_stats'].keys()):
                stats = summary['channel_stats'][ch]
                print(f"  通道{ch}:")
                print(f"    总数: {stats['total']} | 成功: {stats['success']} | 失败: {stats['fail']} | 成功率: {stats['success_rate']:.2f}%")
            
            if summary['error_types']:
                print(f"\n错误类型统计:")
                for err_type, count in sorted(summary['error_types'].items()):
                    print(f"  {err_type}: {count}")
            
            print(f"{'='*80}\n")
            
    def _print_final_report(self):
        """打印最终测试报告"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 80)
        print("测试最终报告")
        print("=" * 80)
        print(f"测试总时长: {elapsed:.2f}秒")
        
        summary = self.stats.get_summary()
        
        print(f"\n总体统计:")
        print(f"  总操作数: {summary['total_operations']}")
        print(f"  成功操作: {summary['successful_operations']}")
        print(f"  失败操作: {summary['failed_operations']}")
        print(f"  成功率: {summary['success_rate']:.2f}%")
        print(f"  失败率: {summary['fail_rate']:.2f}%")
        
        if summary['total_operations'] > 0:
            ops_per_sec = summary['total_operations'] / elapsed if elapsed > 0 else 0
            print(f"  操作速率: {ops_per_sec:.2f} 操作/秒")
        
        print(f"\n按操作类型统计:")
        for op, stats in sorted(summary['operation_stats'].items()):
            print(f"  {op}:")
            print(f"    总数: {stats['total']}")
            print(f"    成功: {stats['success']} ({stats['success_rate']:.2f}%)")
            print(f"    失败: {stats['fail']} ({100 - stats['success_rate']:.2f}%)")
        
        print(f"\n按通道统计:")
        for ch in sorted(summary['channel_stats'].keys()):
            stats = summary['channel_stats'][ch]
            print(f"  通道{ch}:")
            print(f"    总数: {stats['total']}")
            print(f"    成功: {stats['success']} ({stats['success_rate']:.2f}%)")
            print(f"    失败: {stats['fail']} ({100 - stats['success_rate']:.2f}%)")
        
        if summary['error_types']:
            print(f"\n错误类型统计:")
            total_errors = sum(summary['error_types'].values())
            for err_type, count in sorted(summary['error_types'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_errors * 100) if total_errors > 0 else 0
                print(f"  {err_type}: {count} ({percentage:.2f}%)")
        
        print("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartUSBHub 成功率测试程序')
    parser.add_argument('--channels', type=int, nargs='+', default=[1, 2, 3, 4],
                        help='要测试的通道列表 (默认: 1 2 3 4)')
    parser.add_argument('--sleep-after-on', type=float, default=0.01,
                        help='开启电源后的等待时间（秒）(默认: 0.01)')
    parser.add_argument('--sleep-after-off', type=float, default=0.01,
                        help='关闭电源后的等待时间（秒）(默认: 0.01)')
    parser.add_argument('--duration', type=int, default=None,
                        help='测试持续时间（秒），不指定则无限运行')
    parser.add_argument('--max-iterations', type=int, default=None,
                        help='每个进程的最大迭代次数，不指定则无限运行')
    parser.add_argument('--report-interval', type=int, default=10,
                        help='统计报告间隔（秒）(默认: 10)')
    
    args = parser.parse_args()
    
    manager = TestManager()
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    manager.run_test(
        channels=args.channels,
        sleep_after_on=args.sleep_after_on,
        sleep_after_off=args.sleep_after_off,
        duration=args.duration,
        max_iterations=args.max_iterations,
        report_interval=args.report_interval
    )


if __name__ == "__main__":
    main()

