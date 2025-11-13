import os
import re
import subprocess


def is_device_online(ip):
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '500', ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1
        )
        return result.returncode == 0
    except Exception:
        return False


def get_mac_address(ip):
    """Get MAC address for a given IP from ARP table"""
    try:
        result = os.popen("arp -a").read()
        pattern = rf"{re.escape(ip)}\s+([\da-fA-F]{{2}}-[\da-fA-F]{{2}}-[\da-fA-F]{{2}}-[\da-fA-F]{{2}}-[\da-fA-F]{{2}}-[\da-fA-F]{{2}})"
        match = re.search(pattern, result)
        if match:
            mac = match.group(1).replace('-', ':').upper()
            return mac
    except Exception as e:
        print(f"Error getting MAC for {ip}: {e}")
    return None


def get_connected_devices():
    """Get all devices from ARP table (connected to local network)"""
    result = os.popen("arp -a").read()
    
    devices = []
    hotspot_devices = []
    current_interface = None
    
    for line in result.split('\n'):
        if 'Interface:' in line:
            current_interface = line
            continue
            
        if 'Internet Address' in line or 'Physical Address' in line:
            continue
            
        match = re.search(r'\s+(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2})\s+(\w+)', line)
        if match:
            ip = match.group(1)
            mac = match.group(2)
            conn_type = match.group(3)
            
            if ip.endswith('.255'):
                continue
            if ip.startswith('224.') or ip.startswith('239.'):
                continue
            
            is_hotspot = ip.startswith('192.168.137.')
            
            if is_hotspot or conn_type == 'dynamic':
                if is_hotspot:
                    hotspot_devices.append(ip)
                else:
                    devices.append(ip)
    
    return hotspot_devices + devices if hotspot_devices else devices


if __name__ == "__main__":
    print("Connected Devices:", get_connected_devices())
