import threading
import time
import sys
import os

# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub

# 命令间隔延迟时间（秒），用于避免命令发送过快导致MCU状态机混乱
# 可以根据测试需要调整此值，例如：0.001 (1ms), 0.010 (10ms), 0.020 (20ms) 等
# 注意：当 ENABLE_SYNC_LOCK = False 时，建议使用 20ms 或更大的延迟
COMMAND_DELAY = 0.020  # 默认20ms延迟，确保MCU有足够时间处理命令和发送ACK响应


def stress_test(total_iterations: int = 10_000_000, channels=(1, 2, 3, 4)) -> None:
    """Run a concurrent stress test on the SmartUSBHub for a given number of toggle cycles.

    This function connects to the first available SmartUSBHub and spawns one thread per channel.
    Each thread repeatedly toggles the power on its assigned channel on and off, counting cycles.
    The test stops once the total number of cycles across all channels reaches ``total_iterations``.

    During the test, a progress printer thread outputs the current number of completed cycles and
    success/failure counts every second.

    Note: When ENABLE_SYNC_LOCK = False, this test can cause MCU state machine issues due to
    concurrent command sending. The test includes small delays to mitigate this, but for production
    use, ENABLE_SYNC_LOCK should be set to True.

    Args:
        total_iterations: Total number of on/off toggle cycles to perform across all channels.
        channels: A tuple of channel numbers to test.
    """
    hub = SmartUSBHub.scan_and_connect()
    if hub is None:
        print("No Smart USB Hub found. Exiting stress test.")
        return

    # Shared counters
    iteration_counts = {ch: 0 for ch in channels}
    success_count = 0
    failure_count = 0
    global_count = 0
    count_lock = threading.Lock()

    def worker(ch: int) -> None:
        nonlocal global_count, success_count, failure_count
        while True:
            with count_lock:
                if global_count >= total_iterations:
                    break
                global_count += 1
            # Turn the channel on and check status
            ok_on = hub.set_channel_power(ch, state=1)
            time.sleep(COMMAND_DELAY)
            hub.get_channel_power_status(ch)
            time.sleep(COMMAND_DELAY)
            # Turn the channel off and check status
            ok_off = hub.set_channel_power(ch, state=0)
            time.sleep(COMMAND_DELAY)
            hub.get_channel_power_status(ch)
            time.sleep(COMMAND_DELAY)
            with count_lock:
                iteration_counts[ch] += 1
                # Record a success only if both on and off operations were acknowledged
                if ok_on and ok_off:
                    success_count += 1
                else:
                    failure_count += 1

    def progress_printer() -> None:
        """Print progress and success/failure counts once per second."""
        while True:
            time.sleep(1)
            with count_lock:
                current = global_count
                succ = success_count
                fail = failure_count
            print(f"Progress: {current}/{total_iterations} cycles, Success: {succ}, Failure: {fail}")
            if current >= total_iterations:
                break

    # Start worker threads for each channel
    worker_threads = []
    for ch in channels:
        t = threading.Thread(target=worker, args=(ch,), daemon=True)
        worker_threads.append(t)
        t.start()

    # Start the progress printer thread
    printer_thread = threading.Thread(target=progress_printer, daemon=True)
    printer_thread.start()

    # Wait for all worker threads to complete
    for t in worker_threads:
        t.join()
    # Ensure the progress printer has finished
    printer_thread.join()

    # Final report
    print(f"Stress test completed. Total cycles: {global_count}, Success: {success_count}, Failure: {failure_count}")


if __name__ == "__main__":
    # By default run a 10 million cycle stress test
    stress_test()
