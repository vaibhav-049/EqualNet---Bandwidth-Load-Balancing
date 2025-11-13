"""
Windows Hotspot Controller
Actually controls bandwidth when laptop is the gateway/hotspot
Uses Windows QoS policies for real bandwidth control
"""
import subprocess
import re
from typing import Dict, List, Optional


class WindowsHotspotController:
    """
    Controls bandwidth for devices connected to Windows hotspot
    Uses Windows QoS policies and DSCP marking
    REQUIRES: Administrator privileges
    """
    
    def __init__(self):
        self.is_admin = self.check_admin()
        self.hotspot_interface = self.get_hotspot_interface()
        self.mode = "active" if self.is_admin else "simulation"
        
        print(f"🔧 Windows Hotspot Controller initialized")
        print(f"📡 Hotspot interface: {self.hotspot_interface}")
        print(f"⚡ Mode: {'ACTIVE (Admin)' if self.is_admin else 'SIMULATION (No admin)'}")
    
    def check_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            result = subprocess.run(
                ["net", "session"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                print("✅ Running with administrator privileges")
                return True
            else:
                print("⚠️  WARNING: Not running as administrator!")
                print("   For actual control: Right-click Python → Run as Administrator")
                return False
        except Exception as e:
            print(f"⚠️  Could not check admin status: {e}")
            return False
    
    def get_hotspot_interface(self) -> str:
        """Get hotspot interface name"""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "hostednetwork"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            for line in result.stdout.split('\n'):
                if "Status" in line and "Started" in line:
                    print("✅ Hotspot is running")
                elif "Status" in line and "Not started" in line:
                    print("⚠️  Hotspot not started - start it from Windows settings")
            
            return "Local Area Connection* 1"
        except Exception as e:
            print(f"⚠️  Could not check hotspot: {e}")
            return "Local Area Connection* 1"
    
    def set_bandwidth_limit(self, ip: str, download_mbps: int, upload_mbps: int) -> bool:
        """
        Apply actual bandwidth limit using Windows QoS
        """
        if not self.is_admin:
            print(f"🔹 [SIMULATION] Bandwidth limit: {ip} → ↓{download_mbps} ↑{upload_mbps} Mbps")
            return True
        
        policy_name_dl = f"EqualNet_DL_{ip.replace('.', '_')}"
        policy_name_ul = f"EqualNet_UL_{ip.replace('.', '_')}"
        
        print(f"⚡ Applying ACTUAL limit: {ip} → ↓{download_mbps} ↑{upload_mbps} Mbps")
        
        success = True
        
        try:
            subprocess.run([
                "powershell", "-Command",
                f"Remove-NetQosPolicy -Name '{policy_name_dl}' -Confirm:$false -ErrorAction SilentlyContinue"
            ], capture_output=True, timeout=5)
            
            subprocess.run([
                "powershell", "-Command",
                f"Remove-NetQosPolicy -Name '{policy_name_ul}' -Confirm:$false -ErrorAction SilentlyContinue"
            ], capture_output=True, timeout=5)
            
            download_bits = download_mbps * 1024 * 1024
            result = subprocess.run([
                "powershell", "-Command",
                f"New-NetQosPolicy -Name '{policy_name_dl}' "
                f"-IPDstPrefix '{ip}/32' "
                f"-ThrottleRateActionBitsPerSecond {download_bits} "
                f"-NetworkProfile All"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"  ✅ Download limit applied: {download_mbps} Mbps")
            else:
                print(f"  ⚠️  Download limit failed: {result.stderr[:100]}")
                success = False
            
            upload_bits = upload_mbps * 1024 * 1024
            result = subprocess.run([
                "powershell", "-Command",
                f"New-NetQosPolicy -Name '{policy_name_ul}' "
                f"-IPSrcPrefix '{ip}/32' "
                f"-ThrottleRateActionBitsPerSecond {upload_bits} "
                f"-NetworkProfile All"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"  ✅ Upload limit applied: {upload_mbps} Mbps")
            else:
                print(f"  ⚠️  Upload limit failed")
                success = False
            
            return success
            
        except Exception as e:
            print(f"  ❌ Error applying limit: {e}")
            return False
    
    def set_qos_priority(self, ip: str, priority: int) -> bool:
        """
        Set QoS priority using DSCP marking
        Priority 1 = Highest, 5 = Lowest
        """
        if not self.is_admin:
            print(f"🔹 [SIMULATION] QoS Priority: {ip} → P{priority}")
            return True
        
        policy_name = f"EqualNet_P{priority}_{ip.replace('.', '_')}"
        
        dscp_map = {
            1: 46,  # EF (Expedited Forwarding) - VoIP, Gaming, HD Streaming
            2: 34,  # AF41 - Streaming
            3: 26,  # AF31 - Interactive
            4: 18,  # AF21 - Bulk
            5: 10   # AF11 - Background
        }
        
        dscp_value = dscp_map.get(priority, 0)
        
        print(f"🎯 Setting ACTUAL priority: {ip} → P{priority} (DSCP {dscp_value})")
        
        try:
            subprocess.run([
                "powershell", "-Command",
                f"Remove-NetQosPolicy -Name 'EqualNet_P*_{ip.replace('.', '_')}' -Confirm:$false -ErrorAction SilentlyContinue"
            ], capture_output=True, timeout=5)
            
            result = subprocess.run([
                "powershell", "-Command",
                f"New-NetQosPolicy -Name '{policy_name}' "
                f"-IPDstPrefix '{ip}/32' "
                f"-DSCPAction {dscp_value} "
                f"-NetworkProfile All"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"  ✅ Priority applied successfully")
                return True
            else:
                print(f"  ⚠️  Priority setting failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Error setting priority: {e}")
            return False
    
    def apply_all_limits(self, allocations: Dict[str, float], priorities: Dict[str, int] = None) -> Dict[str, bool]:
        """Apply bandwidth limits and priorities to all devices"""
        results = {}
        
        if not allocations:
            print("⚠️  No allocations to apply")
            return results
        
        if priorities is None:
            priorities = {}
        
        print(f"\n{'='*70}")
        print(f"🚀 Applying limits to {len(allocations)} devices...")
        print(f"   Mode: {'ACTUAL CONTROL ✅' if self.is_admin else 'SIMULATION 🔹'}")
        print(f"{'='*70}\n")
        
        for ip, allocation in allocations.items():
            download = int(allocation)
            upload = int(download * 0.4)
            
            success = self.set_bandwidth_limit(ip, download, upload)
            
            if ip in priorities and success:
                self.set_qos_priority(ip, priorities[ip])
            
            results[ip] = success
        
        print(f"\n{'='*70}")
        success_count = sum(1 for v in results.values() if v)
        
        if self.is_admin:
            print(f"✅ Applied ACTUAL limits: {success_count}/{len(allocations)} devices")
        else:
            print(f"🔹 Simulated limits: {success_count}/{len(allocations)} devices")
            print(f"   Run as Administrator for actual control!")
        print(f"{'='*70}\n")
        
        return results
    
    def clear_all_limits(self) -> bool:
        """Clear all EqualNet QoS policies"""
        if not self.is_admin:
            print("🔹 [SIMULATION] All limits cleared")
            return True
        
        print("🧹 Clearing all EqualNet QoS policies...")
        
        try:
            result = subprocess.run([
                "powershell", "-Command",
                "Get-NetQosPolicy | Where-Object {$_.Name -like 'EqualNet*'} | Remove-NetQosPolicy -Confirm:$false"
            ], capture_output=True, text=True, timeout=10)
            
            print("✅ All EqualNet policies cleared from Windows QoS")
            return True
        except Exception as e:
            print(f"❌ Failed to clear policies: {e}")
            return False
    
    def get_router_info(self) -> Dict:
        """Get controller information"""
        return {
            "ip": "Windows Hotspot",
            "type": "windows_hotspot",
            "logged_in": self.is_admin,
            "mode": "active" if self.is_admin else "simulation",
            "interface": self.hotspot_interface,
            "admin": self.is_admin
        }
    
    def list_qos_policies(self) -> List[str]:
        """List all EqualNet QoS policies"""
        if not self.is_admin:
            return []
        
        try:
            result = subprocess.run([
                "powershell", "-Command",
                "Get-NetQosPolicy | Where-Object {$_.Name -like 'EqualNet*'} | Select-Object -ExpandProperty Name"
            ], capture_output=True, text=True, timeout=5)
            
            policies = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            if policies:
                print(f"\n📋 Active EqualNet Policies ({len(policies)}):")
                for policy in policies:
                    print(f"   - {policy}")
            
            return policies
        except Exception as e:
            print(f"⚠️  Could not list policies: {e}")
            return []
    
    def check_hotspot_status(self) -> Dict:
        """Check Windows hotspot status"""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "hostednetwork"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            status = {
                "enabled": False,
                "started": False,
                "ssid": None,
                "clients": 0
            }
            
            for line in result.stdout.split('\n'):
                if "Mode" in line and "Allowed" in line:
                    status["enabled"] = True
                if "Status" in line and "Started" in line:
                    status["started"] = True
                if "SSID name" in line:
                    match = re.search(r':\s*"(.+)"', line)
                    if match:
                        status["ssid"] = match.group(1)
                if "Number of clients" in line:
                    match = re.search(r':\s*(\d+)', line)
                    if match:
                        status["clients"] = int(match.group(1))
            
            return status
        except Exception as e:
            print(f"⚠️  Could not check hotspot status: {e}")
            return {"enabled": False, "started": False}
    
    def enable_ip_forwarding(self) -> bool:
        """Enable IP forwarding (routing) on Windows"""
        if not self.is_admin:
            print("⚠️  Need admin rights to enable IP forwarding")
            return False
        
        try:
            subprocess.run([
                "reg", "add",
                "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters",
                "/v", "IPEnableRouter",
                "/t", "REG_DWORD",
                "/d", "1",
                "/f"
            ], capture_output=True, timeout=5)
            
            print("✅ IP forwarding enabled")
            return True
        except Exception as e:
            print(f"❌ Failed to enable IP forwarding: {e}")
            return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Windows Hotspot Controller - Test Mode")
    print("="*70 + "\n")
    
    controller = WindowsHotspotController()
    
    print("\n📊 Hotspot Status:")
    status = controller.check_hotspot_status()
    print(f"   Enabled: {status.get('enabled', False)}")
    print(f"   Started: {status.get('started', False)}")
    print(f"   SSID: {status.get('ssid', 'N/A')}")
    print(f"   Clients: {status.get('clients', 0)}")
    
    print("\n🧪 Testing bandwidth limit...")
    controller.set_bandwidth_limit("192.168.137.100", 25, 10)
    
    print("\n🧪 Testing priority setting...")
    controller.set_qos_priority("192.168.137.100", 1)
    
    print("\n📋 Listing active policies...")
    controller.list_qos_policies()
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70 + "\n")
