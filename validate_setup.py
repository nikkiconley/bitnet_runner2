#!/usr/bin/env python3
"""
Validation script for BitNet MQTT Device setup
"""

import sys
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required, found:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required = ['paho.mqtt.client', 'requests', 'cryptography']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('.', '/').replace('/', '.'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    return len(missing) == 0

def check_config_file():
    """Check if configuration file exists and is valid"""
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        required_keys = ['mqtt', 'cert_service_url', 'bitnet_path']
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required config key: {key}")
                return False
        
        print("✅ config.json is valid")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False

def check_bitnet_path():
    """Check if BitNet path exists"""
    try:
        with open("config.json") as f:
            config = json.load(f)
        
        bitnet_path = Path(config.get('bitnet_path', '../BitNet'))
        if bitnet_path.exists():
            print(f"✅ BitNet path exists: {bitnet_path}")
            return True
        else:
            print(f"❌ BitNet path not found: {bitnet_path}")
            return False
    except:
        print("❌ Could not check BitNet path")
        return False

def check_network_connectivity():
    """Check if device can reach the certificate service"""
    try:
        with open("config.json") as f:
            config = json.load(f)
        
        cert_service = config.get('cert_service_url', '')
        if not cert_service:
            print("❌ No certificate service URL configured")
            return False
        
        import requests
        response = requests.get(cert_service, timeout=10)
        if response.status_code == 200:
            print(f"✅ Certificate service reachable: {cert_service}")
            return True
        else:
            print(f"⚠️  Certificate service returned {response.status_code}: {cert_service}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach certificate service: {e}")
        return False

def check_device_script():
    """Check if the main device script runs"""
    try:
        result = subprocess.run([
            sys.executable, 'bitnet_mqtt_device.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Device script runs correctly")
            return True
        else:
            print(f"❌ Device script failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Cannot run device script: {e}")
        return False

def main():
    """Run all validation checks"""
    print("BitNet MQTT Device Validation")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config_file),
        ("BitNet Path", check_bitnet_path),
        ("Network Connectivity", check_network_connectivity),
        ("Device Script", check_device_script)
    ]
    
    passed = 0
    for name, check_func in checks:
        print(f"\n{name}:")
        if check_func():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Validation Results: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("🎉 All checks passed! Device is ready.")
        print("\nNext steps:")
        print("1. Register device: python3 bitnet_mqtt_device.py --config config.json register")
        print("2. Start service: ./start_service.sh")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
