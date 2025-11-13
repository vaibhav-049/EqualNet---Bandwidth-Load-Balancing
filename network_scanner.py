"""
Network Scanner - Actively scans subnet for all devices
"""
import subprocess
import threading
import re
from typing import List, Tuple


def get_local_ip_and_subnet():
    """Get local IP address and calculate subnet (prefer WiFi adapter)"""
    try:
        result = subprocess.run(
            ['ipconfig'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.split('\n')
        all_ips = []
        
        for i, line in enumerate(lines):
            if 'IPv4 Address' in line and '192.168.' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if not (ip.startswith('192.168.56.') or 
                            ip.startswith('192.168.47.')):
                        all_ips.append(ip)
        
        if all_ips:
            ip = all_ips[0]
            parts = ip.split('.')
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
            return ip, subnet
            
    except Exception as e:
        print(f"Error getting local IP: {e}")
    
    return None, None


def ping_host(ip: str, results: List[Tuple[str, bool]]):
    """Ping a single host and store result"""
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '300', ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1
        )
        if result.returncode == 0:
            results.append((ip, True))
    except Exception:
        pass


def scan_subnet(subnet: str = None, start: int = 1, end: int = 254) -> List[str]:
    """
    Scan a subnet for active devices
    
    Args:
        subnet: Subnet to scan (e.g., "192.168.29")
        start: Starting host number (default: 1)
        end: Ending host number (default: 254)
    
    Returns:
        List of active IP addresses
    """
    if not subnet:
        local_ip, subnet = get_local_ip_and_subnet()
        if not subnet:
            print("❌ Could not determine local subnet")
            return []
        print(f"📡 Scanning subnet {subnet}.0/24 ...")
    
    results = []
    threads = []
    
    for i in range(start, end + 1):
        ip = f"{subnet}.{i}"
        thread = threading.Thread(target=ping_host, args=(ip, results))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        
        if len(threads) >= 50:
            for t in threads:
                t.join(timeout=2)
            threads = []
    
    for thread in threads:
        thread.join(timeout=2)
    
    active_ips = sorted([ip for ip, active in results if active],
                       key=lambda x: [int(p) for p in x.split('.')])
    
    print(f"✅ Found {len(active_ips)} active devices")
    return active_ips


def get_all_network_devices() -> List[str]:
    """
    Get all devices on local network using ARP + active scanning
    
    Returns:
        List of all device IPs (from ARP + scan)
    """
    import monitor
    
    arp_devices = set(monitor.get_connected_devices())
    
    local_ip, subnet = get_local_ip_and_subnet()
    if local_ip:
        arp_devices.discard(local_ip)
    
    print(f"📋 ARP table has {len(arp_devices)} devices")
    
    if subnet:
        print(f"🔍 Quick scanning {subnet}.0/24 ...")
        common_ips = [1, 254]  # Router/Gateway IPs
        
        scan_results = scan_subnet(subnet, 1, 254)
        
        all_devices = arp_devices.union(set(scan_results))
        
        if local_ip:
            all_devices.discard(local_ip)
        
        return sorted(list(all_devices),
                     key=lambda x: [int(p) for p in x.split('.')])
    
    return sorted(list(arp_devices),
                 key=lambda x: [int(p) for p in x.split('.')])


if __name__ == "__main__":
    import monitor
    
    print("🔍 EqualNet Network Scanner")
    print("=" * 50)
    
    devices = get_all_network_devices()
    
    print("\n📱 Connected Devices:")
    print("-" * 50)
    for i, ip in enumerate(devices, 1):
        mac = monitor.get_mac_address(ip)
        print(f"{i}. {ip:15s}  {mac or 'No MAC'}")
    
    print(f"\n✅ Total: {len(devices)} devices found")
