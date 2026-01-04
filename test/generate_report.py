"""
生成测试报告的便捷脚本

使用方法:
    python test/generate_report.py                    # 生成常规测试报告
    python test/generate_report.py --stress          # 生成压力测试报告
    python test/generate_report.py --all             # 生成所有测试报告
    python test/generate_report.py --stress --open   # 生成压力测试报告并自动打开
"""
import sys
import os
import subprocess
import webbrowser
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def generate_report(test_file=None, open_browser=False):
    """生成测试报告"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建 pytest 命令
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "--html=report.html",
        "--self-contained-html",
        "--log-cli-level=INFO"
    ]
    
    if test_file:
        cmd.append(test_file)
    else:
        # 默认运行所有测试
        cmd.append(".")
    
    print(f"正在生成测试报告...")
    print(f"命令: {' '.join(cmd)}")
    print()
    
    # 运行测试
    result = subprocess.run(cmd, cwd=test_dir)
    
    report_path = os.path.join(test_dir, "report.html")
    
    if os.path.exists(report_path):
        print(f"\n✓ 测试报告已生成: {report_path}")
        print(f"  文件大小: {os.path.getsize(report_path) / 1024:.1f} KB")
        
        if open_browser:
            print(f"正在打开报告...")
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        
        return True
    else:
        print(f"\n✗ 测试报告生成失败")
        return False

def main():
    parser = argparse.ArgumentParser(description="生成 pytest HTML 测试报告")
    parser.add_argument("--stress", action="store_true", help="只运行压力测试")
    parser.add_argument("--integration", action="store_true", help="只运行常规集成测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--open", action="store_true", help="生成后自动打开报告")
    
    args = parser.parse_args()
    
    test_file = None
    if args.stress:
        test_file = "test_integration_stress.py"
        print("=" * 70)
        print("生成压力测试报告")
        print("=" * 70)
    elif args.integration:
        test_file = "test_integration.py"
        print("=" * 70)
        print("生成常规集成测试报告")
        print("=" * 70)
    elif args.all:
        test_file = None
        print("=" * 70)
        print("生成所有测试报告")
        print("=" * 70)
    else:
        # 默认运行常规测试
        test_file = "test_integration.py"
        print("=" * 70)
        print("生成常规集成测试报告（默认）")
        print("=" * 70)
        print("提示: 使用 --stress 生成压力测试报告，使用 --all 生成所有测试报告")
        print("=" * 70)
    
    success = generate_report(test_file, args.open)
    
    if success:
        print("\n提示: 报告文件位于 test/report.html")
        if not args.open:
            print("      使用 --open 参数可以自动打开报告")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()


