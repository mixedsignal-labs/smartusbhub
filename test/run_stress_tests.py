"""
快速运行压力测试的便捷脚本

使用方法:
    python test/run_stress_tests.py                    # 运行所有压力测试并自动打开HTML报告
    python test/run_stress_tests.py --quick            # 快速测试（跳过极限测试）并自动打开HTML报告
    python test/run_stress_tests.py --single           # 只运行单通道测试并自动打开HTML报告
    python test/run_stress_tests.py --all-channels     # 只运行所有通道测试并自动打开HTML报告
    python test/run_stress_tests.py --no-open          # 运行测试但不自动打开报告
"""
import pytest
import sys
import os
import argparse

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行 SmartUSBHub 压力测试")
    parser.add_argument("--quick", action="store_true", help="快速测试（跳过极限测试）")
    parser.add_argument("--single", action="store_true", help="只运行单通道压力测试")
    parser.add_argument("--all-channels", action="store_true", help="只运行所有通道压力测试")
    parser.add_argument("--no-open", action="store_true", help="不自动打开HTML报告（默认会自动打开）")
    args = parser.parse_args()
    
    test_file = os.path.join(os.path.dirname(__file__), "test_integration_stress.py")
    
    pytest_args = [
        test_file,
        "-v", "-s",  # 详细输出，显示print/log
        "--log-cli-level=INFO",  # 显示INFO级别日志
    ]
    
    if args.quick:
        # 快速测试：跳过极限测试和100万次测试
        pytest_args.extend(["-k", "not extreme_stress and not read_stability"])
        print("运行快速压力测试（跳过极限测试和长时间测试）...")
    elif args.single:
        # 只运行单通道测试
        pytest_args.append("::test_high_speed_single_channel_power")
        print("运行单通道压力测试...")
    elif args.all_channels:
        # 只运行所有通道测试
        pytest_args.append("::test_high_speed_all_channels_power")
        print("运行所有通道压力测试...")
    else:
        print("运行所有压力测试（可能需要较长时间）...")
        print("提示：使用 --quick 进行快速测试，或 --single/--all-channels 运行特定测试")
    
    # 默认总是生成HTML报告
    report_path = os.path.join(os.path.dirname(__file__), "report_stress.html")
    pytest_args.extend([
        "--html", report_path,
        "--self-contained-html"
    ])
    print(f"将生成HTML报告: {report_path}")
    
    print("\n" + "="*70)
    print("开始运行压力测试...")
    print("="*70 + "\n")
    
    exit_code = pytest.main(pytest_args)
    
    # 测试完成后，如果报告存在，自动打开（除非指定了 --no-open）
    if not args.no_open:
        if os.path.exists(report_path):
            print(f"\n✓ HTML报告已生成: {report_path}")
            try:
                import webbrowser
                webbrowser.open_new_tab(f"file:///{os.path.abspath(report_path)}")
                print("✓ 已在浏览器中打开报告")
            except Exception as e:
                print(f"⚠ 无法自动打开浏览器: {e}")
                print(f"  请手动打开: {os.path.abspath(report_path)}")
        else:
            print(f"\n⚠ 报告文件未找到: {report_path}")
    
    sys.exit(exit_code)

