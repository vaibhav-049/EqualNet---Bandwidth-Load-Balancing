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
        # Pattern to match IP and MAC in Windows ARP output
        # Format: 192.168.1.100    aa-bb-cc-dd-ee-ff     dynamic
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
    
    # Find all interface sections
    devices = []
    current_interface = None
    
    for line in result.split('\n'):
        # Check if this is an interface line
        if 'Interface:' in line:
            current_interface = line
            continue
            
        # Skip header lines
        if 'Internet Address' in line or 'Physical Address' in line:
            continue
            
        # Parse device lines (IP + MAC + Type)
        # Format: "  192.168.29.90     14-13-33-e2-e4-f9     dynamic"
        match = re.search(r'\s+(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2}-[\da-fA-F]{2})\s+(\w+)', line)
        if match:
            ip = match.group(1)
            mac = match.group(2)
            conn_type = match.group(3)
            
            # Skip broadcast, multicast, and gateway (but check activity later)
            if ip.endswith('.255'):
                continue
            if ip.startswith('224.') or ip.startswith('239.'):
                continue
            
            # Only include dynamic entries (not static)
            if conn_type == 'dynamic':
                devices.append(ip)
    
    return devices


if __name__ == "__main__":
    print("Connected Devices:", get_connected_devices())
