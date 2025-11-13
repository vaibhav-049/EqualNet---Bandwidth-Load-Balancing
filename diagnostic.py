"""
EqualNet Diagnostic Tool
Checks system configuration for Windows Hotspot QoS control
"""

import subprocess
import sys
import ctypes
import platform

def is_admin():
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print("✅ Python version OK")
        return True
    else:
        print("❌ Python 3.7+ required")
        return False

def check_windows_version():
    """Check Windows version"""
    version = platform.version()
    print(f"Windows Version: {version}")
    if int(platform.version().split('.')[0]) >= 10:
        print("✅ Windows 10+ detected")
        return True
    else:
        print("❌ Windows 10+ required for QoS")
        return False

def check_dependencies():
    """Check required Python packages"""
    required = ['flask', 'flask_cors', 'psutil', 'scapy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    return len(missing) == 0

def check_hotspot_mode():
    """Check if hotspot mode is enabled"""
    try:
        with open('api_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'HOTSPOT_MODE = True' in content:
                print("✅ Hotspot mode ENABLED (ACTUAL control)")
                return True
            else:
                print("⚠️ Hotspot mode DISABLED (simulation only)")
                return False
    except Exception as e:
        print(f"❌ Could not check config: {e}")
        return False

def check_qos_policies():
    """Check existing QoS policies"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             "Get-NetQosPolicy | Where-Object {$_.Name -like 'EqualNet_*'} | Measure-Object"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'Count' in result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'Count' in line:
                    count = line.split(':')[1].strip()
                    print(f"📊 Existing QoS policies: {count}")
                    return True
        
        print("📊 No existing QoS policies found")
        return True
    except Exception as e:
        print(f"⚠️ Could not check QoS policies: {e}")
        return False

def check_hotspot_status():
    """Check if Windows hotspot is enabled"""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*Wi-Fi*' -or $_.InterfaceDescription -like '*Local Area Connection*'} | Select-Object -First 1 Name"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            adapter = result.stdout.strip().split('\n')[-1]
            print(f"✅ Network adapter found: {adapter}")
            return True
        else:
            print("⚠️ No hotspot adapter detected")
            print("   Enable Mobile Hotspot in Windows Settings")
            return False
    except Exception as e:
        print(f"⚠️ Could not check hotspot status: {e}")
        return False

def main():
    print("=" * 60)
    print("EqualNet System Diagnostic")
    print("=" * 60)
    print()
    
    print("🔐 Administrator Privileges:")
    if is_admin():
        print("✅ Running as administrator")
    else:
        print("❌ NOT running as administrator")
        print("   QoS policies require admin rights!")
        print("   Right-click and 'Run as administrator'")
    print()
    
    print("💻 System Requirements:")
    python_ok = check_python_version()
    windows_ok = check_windows_version()
    print()
    
    print("📦 Python Dependencies:")
    deps_ok = check_dependencies()
    print()
    
    print("⚙️ Configuration:")
    hotspot_mode = check_hotspot_mode()
    print()
    
    print("🌐 Network Setup:")
    hotspot_ok = check_hotspot_status()
    print()
    
    # QoS status
    print("📊 QoS Status:")
    qos_ok = check_qos_policies()
    print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_ok = all([
        is_admin(),
        python_ok,
        windows_ok,
        deps_ok
    ])
    
    if all_ok:
        print("✅ System ready for EqualNet!")
        print()
        if hotspot_mode:
            if hotspot_ok:
                print("🚀 Ready for ACTUAL bandwidth control!")
                print("   1. Connect devices to your hotspot")
                print("   2. Run: python api_server.py (as admin)")
                print("   3. Open dashboard: http://localhost:5000")
                print("   4. Apply limits from Settings tab")
            else:
                print("⚠️ Enable Windows Mobile Hotspot first:")
                print("   Settings → Network & Internet → Mobile hotspot")
        else:
            print("📝 Currently in router mode (simulation)")
            print("   To enable ACTUAL control:")
            print("   1. Edit api_server.py")
            print("   2. Set HOTSPOT_MODE = True")
            print("   3. Enable Windows Mobile Hotspot")
            print("   4. Restart server as admin")
    else:
        print("❌ Please fix the issues above before proceeding")
    
    print()
    print("=" * 60)
    print("For detailed setup instructions, see: HOTSPOT_SETUP.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
