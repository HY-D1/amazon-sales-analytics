#!/usr/bin/env python3
"""
Health check script for Amazon Sales Analytics
Run: python3 check.py
"""

import sys
import subprocess

def check_python():
    """Check Python version"""
    version = sys.version_info
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("⚠️  Warning: Python 3.9+ recommended")
        return False
    return True

def check_file(filepath, description):
    """Check if file exists"""
    import os
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description} NOT FOUND: {filepath}")
        return False

def check_package(package):
    """Check if package is installed"""
    try:
        __import__(package)
        print(f"✅ {package}")
        return True
    except ImportError:
        print(f"❌ {package} NOT INSTALLED")
        return False

def check_port(port):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    if result == 0:
        print(f"⚠️  Port {port} is in use")
        return False
    else:
        print(f"✅ Port {port} is available")
        return True

def main():
    print("="*60)
    print("📊 Amazon Sales Analytics - Health Check")
    print("="*60)
    
    all_ok = True
    packages_ok = True
    files_ok = True
    
    # Check Python
    print("\n🔧 Python:")
    all_ok &= check_python()
    
    # Check files
    print("\n📁 Files:")
    files_ok &= check_file("data/Amazon.csv", "Data file")
    files_ok &= check_file("dashboard.py", "Dashboard script")
    files_ok &= check_file("notebooks/amazon_sales_analysis.ipynb", "Notebook")
    files_ok &= check_file("requirements.txt", "Requirements")
    files_ok &= check_file("start.sh", "Start script")
    all_ok &= files_ok
    
    # Check packages
    print("\n📦 Core Packages:")
    packages = ['pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'streamlit']
    for pkg in packages:
        if not check_package(pkg):
            packages_ok = False
    all_ok &= packages_ok
    
    # Check ports
    print("\n🌐 Ports:")
    port_8501 = check_port(8501)  # Streamlit default
    port_8888 = check_port(8888)  # Jupyter default
    
    # Summary
    print("\n" + "="*60)
    if all_ok:
        print("✅ All checks passed!")
        print("   Run: ./start.sh")
    else:
        if not packages_ok:
            print("\n❌ Missing packages. Install with:")
            print("   pip install -r requirements.txt")
            print("\n   Or let start.sh handle it:")
            print("   ./start.sh")
        if not files_ok:
            print("\n❌ Missing files. Check that all files are present.")
        if not port_8501:
            print("\n⚠️  Port 8501 is busy. start.sh will auto-find another port.")
    print("="*60)

if __name__ == "__main__":
    main()
