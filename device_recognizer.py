"""
Device Recognition Module
Identifies device types and manufacturers from MAC addresses
"""
import re
import subprocess
import platform
from typing import Dict, Optional


MAC_VENDORS = {
    "00:03:93": "Apple",
    "00:05:02": "Apple",
    "00:0A:27": "Apple",
    "00:0A:95": "Apple",
    "00:0D:93": "Apple",
    "00:10:FA": "Apple",
    "00:11:24": "Apple",
    "00:14:51": "Apple",
    "00:16:CB": "Apple",
    "00:17:F2": "Apple",
    "00:19:E3": "Apple",
    "00:1B:63": "Apple",
    "00:1C:B3": "Apple",
    "00:1D:4F": "Apple",
    "00:1E:52": "Apple",
    "00:1E:C2": "Apple",
    "00:1F:5B": "Apple",
    "00:1F:F3": "Apple",
    "00:21:E9": "Apple",
    "00:22:41": "Apple",
    "00:23:12": "Apple",
    "00:23:32": "Apple",
    "00:23:6C": "Apple",
    "00:23:DF": "Apple",
    "00:24:36": "Apple",
    "00:25:00": "Apple",
    "00:25:4B": "Apple",
    "00:25:BC": "Apple",
    "00:26:08": "Apple",
    "00:26:4A": "Apple",
    "00:26:B0": "Apple",
    "00:26:BB": "Apple",
    "A4:5E:60": "Apple",
    "A8:20:66": "Apple",
    "AC:87:A3": "Apple",
    "B0:34:95": "Apple",
    "B8:09:8A": "Apple",
    "B8:63:4D": "Apple",
    "BC:3B:AF": "Apple",
    "BC:52:B7": "Apple",
    "C0:63:94": "Apple",
    "C8:2A:14": "Apple",
    "C8:69:CD": "Apple",
    "D0:25:98": "Apple",
    "D4:61:9D": "Apple",
    "D8:30:62": "Apple",
    "DC:2B:61": "Apple",
    "E0:B9:BA": "Apple",
    "E4:25:E7": "Apple",
    "E8:8D:28": "Apple",
    "EC:35:86": "Apple",
    "F0:DB:E2": "Apple",
    "F4:0F:24": "Apple",
    "F8:1E:DF": "Apple",
    
    # Samsung
    "00:12:47": "Samsung",
    "00:12:FB": "Samsung",
    "00:13:77": "Samsung",
    "00:15:B9": "Samsung",
    "00:16:32": "Samsung",
    "00:16:6B": "Samsung",
    "00:16:6C": "Samsung",
    "00:17:C9": "Samsung",
    "00:17:D5": "Samsung",
    "00:18:AF": "Samsung",
    "00:1A:8A": "Samsung",
    "00:1B:98": "Samsung",
    "00:1C:43": "Samsung",
    "00:1D:25": "Samsung",
    "00:1E:7D": "Samsung",
    "00:1E:E1": "Samsung",
    "00:1E:E2": "Samsung",
    "00:21:19": "Samsung",
    "00:21:4C": "Samsung",
    "00:23:39": "Samsung",
    "00:23:D6": "Samsung",
    "00:23:D7": "Samsung",
    "00:24:54": "Samsung",
    "00:24:90": "Samsung",
    "00:24:91": "Samsung",
    "00:25:38": "Samsung",
    "00:26:37": "Samsung",
    "00:26:5D": "Samsung",
    "00:26:5F": "Samsung",
    "A0:0B:BA": "Samsung",
    "A0:21:95": "Samsung",
    "B0:72:BF": "Samsung",
    "C0:BD:D1": "Samsung",
    "D0:59:E4": "Samsung",
    "E4:92:FB": "Samsung",
    "E8:50:8B": "Samsung",
    "EC:1F:72": "Samsung",
    
    # Xiaomi
    "00:9E:C8": "Xiaomi",
    "04:02:1F": "Xiaomi",
    "28:6C:07": "Xiaomi",
    "34:CE:00": "Xiaomi",
    "50:8F:4C": "Xiaomi",
    "58:44:98": "Xiaomi",
    "5C:C3:07": "Xiaomi",
    "64:09:80": "Xiaomi",
    "64:B4:73": "Xiaomi",
    "68:DF:DD": "Xiaomi",
    "74:51:BA": "Xiaomi",
    "78:02:F8": "Xiaomi",
    "78:11:DC": "Xiaomi",
    "7C:1D:D9": "Xiaomi",
    "8C:BE:BE": "Xiaomi",
    "98:FA:E3": "Xiaomi",
    "9C:99:A0": "Xiaomi",
    "A0:86:C6": "Xiaomi",
    "AC:C1:EE": "Xiaomi",
    "B0:E2:35": "Xiaomi",
    "C4:0B:CB": "Xiaomi",
    "D4:97:0B": "Xiaomi",
    "F8:8F:CA": "Xiaomi",
    
    # OnePlus
    "AC:37:43": "OnePlus",
    "C4:07:2F": "OnePlus",
    "D0:58:A8": "OnePlus",
    
    # Google/Nest
    "00:1A:11": "Google",
    "3C:5A:B4": "Google",
    "54:60:09": "Google Nest",
    "6C:AD:F8": "Google",
    "A4:77:33": "Google",
    "CC:2D:E0": "Google",
    "F4:F5:D8": "Google",
    
    # Amazon/Echo
    "00:71:47": "Amazon",
    "00:FC:8B": "Amazon",
    "10:AE:60": "Amazon Echo",
    "38:F7:3D": "Amazon",
    "44:65:0D": "Amazon Echo",
    "50:DC:E7": "Amazon",
    "74:C2:46": "Amazon",
    "84:D6:D0": "Amazon",
    "A0:02:DC": "Amazon",
    "B4:7C:9C": "Amazon Echo",
    "F0:27:2D": "Amazon",
    "FC:A6:67": "Amazon",
    
    # TP-Link
    "00:27:19": "TP-Link",
    "50:C7:BF": "TP-Link",
    "60:E3:27": "TP-Link",
    "A4:2B:B0": "TP-Link",
    "C0:4A:00": "TP-Link",
    "F4:F2:6D": "TP-Link",
    
    # Netgear
    "00:09:5B": "Netgear",
    "00:0F:B5": "Netgear",
    "00:14:6C": "Netgear",
    "00:18:4D": "Netgear",
    "00:1B:2F": "Netgear",
    "00:1E:2A": "Netgear",
    "00:22:3F": "Netgear",
    "00:24:B2": "Netgear",
    "00:26:F2": "Netgear",
    "20:E5:2A": "Netgear",
    "28:C6:8E": "Netgear",
    "44:94:FC": "Netgear",
    "48:9E:9D": "Netgear",
    "A0:63:91": "Netgear",
    "C0:3F:0E": "Netgear",
    "E0:46:9A": "Netgear",
    
    # Jio/Reliance
    "F0:ED:B8": "JioFiber",
    "B8:D9:4D": "Jio",
    "C8:B5:AD": "Jio",
    "00:02:76": "Reliance",
    "04:D6:AA": "Reliance Jio",
    "08:ED:B9": "Reliance Jio",
    "20:47:ED": "Reliance Jio",
    "38:D5:47": "Reliance Jio",
    "40:4E:36": "Reliance Jio",
    "48:3B:38": "Reliance Jio",
    "64:A2:F9": "Reliance Jio",
    "88:36:5F": "Reliance Jio",
    "A8:4E:3F": "Reliance Jio",
    "C4:71:54": "Reliance Jio",
    "D8:0F:99": "Reliance Jio",
    "E4:6F:13": "Reliance Jio",
    "F4:A4:D6": "Reliance Jio",
    
    # D-Link
    "00:05:5D": "D-Link",
    "00:0D:88": "D-Link",
    "00:11:95": "D-Link",
    "00:13:46": "D-Link",
    "00:15:E9": "D-Link",
    "00:17:9A": "D-Link",
    "00:19:5B": "D-Link",
    "00:1B:11": "D-Link",
    "00:1C:F0": "D-Link",
    "00:1E:58": "D-Link",
    
    # Raspberry Pi
    "B8:27:EB": "Raspberry Pi",
    "DC:A6:32": "Raspberry Pi",
    "E4:5F:01": "Raspberry Pi",
    
    # Intel
    "00:02:B3": "Intel",
    "00:03:47": "Intel",
    "00:04:23": "Intel",
    "00:07:E9": "Intel",
    "00:0C:F1": "Intel",
    "00:0E:35": "Intel",
    "00:11:11": "Intel",
    "00:12:F0": "Intel",
    "00:13:02": "Intel",
    "00:13:20": "Intel",
    "00:13:CE": "Intel",
    "00:13:E8": "Intel",
    
    # Realtek
    "00:E0:4C": "Realtek",
    "52:54:00": "Realtek",
    "70:4D:7B": "Realtek",
    "00:0C:76": "Realtek",
    
    # MediaTek
    "00:0C:43": "MediaTek",
    "14:13:33": "MediaTek",
    "28:1F:94": "MediaTek",
    "68:DB:F5": "MediaTek",
    "7C:B5:9B": "MediaTek",
    "8C:79:F5": "MediaTek",
    "94:65:2D": "MediaTek",
    
    # VirtualBox
    "08:00:27": "VirtualBox",
    "0A:00:27": "VirtualBox",
    
    # Microsoft
    "00:03:FF": "Microsoft",
    "00:0D:3A": "Microsoft",
    "00:12:5A": "Microsoft",
    "00:15:5D": "Microsoft",
    "00:17:FA": "Microsoft",
    "00:50:F2": "Microsoft",
    "28:18:78": "Microsoft",
    "7C:ED:8D": "Microsoft",
    "E0:D5:5E": "Microsoft",
    "A0:48:1C": "Microsoft",
    
    # Dell
    "00:06:5B": "Dell",
    "00:08:74": "Dell",
    "00:0B:DB": "Dell",
    "00:0D:56": "Dell",
    "00:0F:1F": "Dell",
    "00:11:43": "Dell",
    "00:12:3F": "Dell",
    "00:13:72": "Dell",
    "00:14:22": "Dell",
    "B8:2A:72": "Dell",
    "D4:AE:52": "Dell",
    "18:03:73": "Dell",
    
    # HP / Hewlett Packard
    "00:01:E6": "HP",
    "00:01:E7": "HP",
    "00:02:A5": "HP",
    "00:08:83": "HP",
    "00:0A:57": "HP",
    "00:0E:7F": "HP",
    "00:10:83": "HP",
    "00:11:0A": "HP",
    "00:12:79": "HP",
    "00:13:21": "HP",
    "A0:B3:CC": "HP",
    "B4:99:BA": "HP",
    
    # Asus
    "00:0C:6E": "Asus",
    "00:0E:A6": "Asus",
    "00:11:2F": "Asus",
    "00:13:D4": "Asus",
    "00:15:F2": "Asus",
    "00:17:31": "Asus",
    "00:19:DB": "Asus",
    "00:1A:92": "Asus",
    "00:1E:8C": "Asus",
    "04:D4:C4": "Asus",
    "08:60:6E": "Asus",
    
    # Lenovo
    "00:21:CC": "Lenovo",
    "00:23:8B": "Lenovo",
    "40:61:86": "Lenovo",
    "50:3E:AA": "Lenovo",
    "78:45:C4": "Lenovo",
    "B8:AC:6F": "Lenovo",
    "DC:41:A9": "Lenovo",
    
    # Huawei
    "00:18:82": "Huawei",
    "00:1E:10": "Huawei",
    "00:25:9E": "Huawei",
    "00:46:4B": "Huawei",
    "18:68:CB": "Huawei",
    "28:31:52": "Huawei",
    "48:46:FB": "Huawei",
    "6C:4A:85": "Huawei",
    "AC:E2:15": "Huawei",
    "C8:6C:87": "Huawei",
}

DEVICE_PATTERNS = {
    "router": ["router", "gateway", "access point", "ap"],
    "laptop": ["laptop", "notebook", "macbook", "thinkpad"],
    "phone": ["phone", "mobile", "android", "iphone"],
    "tablet": ["tablet", "ipad"],
    "tv": ["tv", "television", "roku", "chromecast", "fire tv"],
    "iot": ["echo", "alexa", "nest", "smart", "iot", "sensor"],
    "gaming": ["playstation", "xbox", "nintendo", "ps4", "ps5"],
    "printer": ["printer", "hp", "canon", "epson"],
}


class DeviceRecognizer:
    def __init__(self):
        self.custom_names = {}
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(
                    ['ipconfig', '/all'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                lines = result.stdout.split('\n')
                found_ip = False
                for i, line in enumerate(lines):
                    if ip in line and 'IPv4' in line:
                        found_ip = True
                        for j in range(i, max(i-15, -1), -1):
                            if 'Physical Address' in lines[j]:
                                mac_match = re.search(
                                    r'([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}',
                                    lines[j]
                                )
                                if mac_match:
                                    mac = mac_match.group(0)
                                    mac = mac.replace('-', ':').upper()
                                    return mac
                
                if not found_ip:
                    subprocess.run(
                        ['ping', '-n', '1', '-w', '100', ip],
                        capture_output=True,
                        timeout=1
                    )
                    
                    result = subprocess.run(
                        ['arp', '-a'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    pattern = rf'{re.escape(ip)}\s+((?:[0-9A-Fa-f]{{2}}-?){{6}})'
                    match = re.search(pattern, result.stdout)
                    if match:
                        mac = match.group(1).replace('-', ':').upper()
                        if len(mac.replace(':', '')) == 12:
                            return mac
        except Exception as e:
            print(f"⚠️ Error getting MAC for {ip}: {e}")
        return None
    
    def get_vendor(self, mac: str) -> str:
        """Get vendor name from MAC address OUI"""
        if not mac:
            return "Unknown"
        
        first_octet = mac.split(':')[0] if ':' in mac else mac[:2]
        try:
            if int(first_octet, 16) & 0x02:  # Locally administered
                return "Private Device"
        except (ValueError, IndexError):
            pass
        
        oui = ':'.join(mac.split(':')[:3]).upper()
        return MAC_VENDORS.get(oui, "Unknown")
    
    def get_device_type(self, vendor: str, hostname: str = "") -> str:
        """Guess device type from vendor and hostname"""
        vendor_lower = vendor.lower()
        hostname_lower = hostname.lower()
        
        combined = f"{vendor_lower} {hostname_lower}"
        
        for device_type, patterns in DEVICE_PATTERNS.items():
            for pattern in patterns:
                if pattern in combined:
                    return device_type
        
        if vendor in ["Apple", "Samsung", "Xiaomi", "OnePlus", "Google", "Huawei"]:
            if "ipad" in hostname_lower or "tablet" in hostname_lower:
                return "tablet"
            return "phone"
        elif vendor in ["TP-Link", "D-Link", "Netgear", "Asus", 
                       "JioFiber", "Jio", "Reliance Jio", "Reliance"]:
            return "router"
        elif vendor == "Private Device":
            return "phone"
        elif vendor in ["Amazon", "Google Nest"]:
            return "iot"
        elif vendor == "Raspberry Pi":
            return "iot"
        elif vendor in ["Dell", "HP", "Lenovo", "Microsoft"]:
            return "laptop"
        elif vendor in ["Intel", "Realtek", "MediaTek"]:
            return "laptop"
        elif vendor == "VirtualBox":
            return "desktop"
        
        return "unknown"
    
    def get_device_icon(self, device_type: str) -> str:
        """Get emoji/icon for device type"""
        icons = {
            "phone": "📱",
            "tablet": "📱",
            "laptop": "💻",
            "desktop": "🖥️",
            "tv": "📺",
            "router": "🌐",
            "iot": "🔌",
            "gaming": "🎮",
            "printer": "🖨️",
            "unknown": "❓"
        }
        return icons.get(device_type, "❓")
    
    def set_custom_name(self, ip: str, name: str):
        """Set custom friendly name for device"""
        self.custom_names[ip] = name
    
    def get_device_info(self, ip: str, hostname: str = "") -> Dict:
        """Get complete device information"""
        mac = self.get_mac_address(ip)
        
        if not mac:
            print(f"⚠️ Could not get MAC address for {ip}")
        
        vendor = self.get_vendor(mac) if mac else "Unknown"
        device_type = self.get_device_type(vendor, hostname)
        icon = self.get_device_icon(device_type)
        
        if ip in self.custom_names:
            friendly_name = self.custom_names[ip]
        else:
            if vendor != "Unknown" and device_type != "unknown":
                friendly_name = f"{vendor} {device_type.title()}"
            elif vendor != "Unknown":
                friendly_name = f"{vendor} Device"
            elif device_type != "unknown":
                friendly_name = f"{device_type.title()} at {ip}"
            else:
                last_octet = ip.split('.')[-1]
                friendly_name = f"Device-{last_octet}"
        
        return {
            "ip": ip,
            "mac": mac or "Unknown",
            "vendor": vendor,
            "device_type": device_type,
            "icon": icon,
            "friendly_name": friendly_name,
            "hostname": hostname
        }


if __name__ == "__main__":
    recognizer = DeviceRecognizer()
    
    import sys
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        info = recognizer.get_device_info(ip)
        print(f"\n{info['icon']} Device Info for {ip}:")
        print(f"  Friendly Name: {info['friendly_name']}")
        print(f"  MAC Address: {info['mac']}")
        print(f"  Vendor: {info['vendor']}")
        print(f"  Type: {info['device_type']}")
    else:
        print("Usage: python device_recognizer.py <ip_address>")
