"""
快速运行压力测试的便捷脚本

使用方法:
    python test/run_stress_tests.py                    # 运行压力测试并自动打开HTML报告
    python test/run_stress_tests.py --no-open          # 运行测试但不自动打开报告
    python test/run_stress_tests.py --no-html         # 不生成HTML报告
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
    parser.add_argument("--no-open", action="store_true", help="不自动打开HTML报告（默认会自动打开）")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    args = parser.parse_args()
    
    test_file = os.path.join(os.path.dirname(__file__), "test_integration_stress.py")
    
    pytest_args = [
        test_file,
        "-v", "-s",  # 详细输出，显示print/log
        "--log-cli-level=INFO",  # 显示INFO级别日志
    ]
    
    print("运行压力测试（核心功能循环测试）...")
    
    # 检查是否安装 pytest-html 插件
    report_path = None
    try:
        import pytest_html
        html_available = True
    except ImportError:
        html_available = False
    
    # 默认总是生成HTML报告（如果插件可用且未指定 --no-html）
    if html_available and not args.no_html:
        report_path = os.path.join(os.path.dirname(__file__), "report_stress.html")
        pytest_args.extend([
            "--html", report_path,
            "--self-contained-html"
        ])
        print(f"将生成HTML报告: {report_path}")
    elif not html_available:
        print("[WARNING] pytest-html 插件未安装，跳过HTML报告生成")
        print("  安装命令: pip install pytest-html")
    
    print("\n" + "="*70)
    print("开始运行压力测试...")
    print("="*70 + "\n")
    
    exit_code = pytest.main(pytest_args)
    
    # 测试完成后，如果报告存在，自动打开（除非指定了 --no-open）
    if not args.no_open and report_path:
        report_abs_path = os.path.abspath(report_path)
        if os.path.exists(report_abs_path):
            print(f"\n[OK] HTML报告已生成: {report_abs_path}")
            try:
                import webbrowser
                # macOS 上需要 file:/// 格式（三个斜杠）
                webbrowser.open(f"file:///{report_abs_path}")
                print("[OK] 已在浏览器中打开报告")
            except Exception as e:
                print(f"[WARNING] 无法自动打开浏览器: {e}")
                print(f"  请手动打开: {report_abs_path}")
        else:
            print(f"\n[WARNING] 报告文件未找到: {report_abs_path}")
    
    sys.exit(exit_code)

