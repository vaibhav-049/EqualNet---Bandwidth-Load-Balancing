# 🚀 Windows Hotspot Setup for ACTUAL Bandwidth Control

This guide explains how to set up your laptop as a network gateway to enable **ACTUAL bandwidth control** using Windows QoS policies.

## 📋 Overview

**Two Modes Available:**
1. **Router Mode** 🔹 - Simulation only (default, requires router API access)
2. **Hotspot Mode** 🔵 - **ACTUAL control** using Windows QoS (this guide)

## 🎯 How Hotspot Mode Works

```
[Phone with Internet] 
        ↓
[Laptop running EqualNet + Windows QoS]  ← ACTUAL CONTROL HERE
        ↓
[Connected Devices] (limited by QoS policies)
```

When your laptop acts as a Wi-Fi hotspot:
- All device traffic flows through your laptop
- Windows QoS policies enforce actual bandwidth limits
- EqualNet calculates fair allocations
- PowerShell NetQoS commands apply real throttling

## 🔧 Setup Instructions

### Step 1: Enable Windows Hotspot

1. **Open Settings:**
   ```
   Windows Key → Settings → Network & Internet → Mobile hotspot
   ```

2. **Configure Hotspot:**
   - Turn on "Share my Internet connection with other devices"
   - Share from: Your internet connection (Ethernet/Wi-Fi)
   - Network name: Choose a name (e.g., "EqualNet-Hotspot")
   - Network password: Set a secure password
   - Network band: 2.4 GHz (better compatibility)

3. **Alternative via PowerShell:**
   ```powershell
   # Enable hotspot
   Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private
   
   # Check current hotspot status
   Get-NetAdapter | Where-Object {$_.InterfaceDescription -like "*Wi-Fi*"}
   ```

### Step 2: Run EqualNet as Administrator

**CRITICAL:** Admin rights are required for QoS policy creation!

**Method 1 - PowerShell (Recommended):**
```powershell
# Navigate to project folder
cd C:\Users\vrajp\Desktop\os_pbl

# Run with admin privileges
Start-Process python -ArgumentList "api_server.py" -Verb RunAs
```

**Method 2 - Right-click menu:**
1. Open Command Prompt/PowerShell as Administrator
2. Navigate to project folder
3. Run: `python api_server.py`

**Method 3 - Create admin shortcut:**
```powershell
# Create a batch file
@echo off
cd C:\Users\vrajp\Desktop\os_pbl
python api_server.py
pause
```
Then: Right-click → Properties → Advanced → Run as administrator

### Step 3: Enable Hotspot Mode in EqualNet

Edit `api_server.py` line 20:
```python
HOTSPOT_MODE = True  # Set to True for actual control
```

**Verify mode on startup:**
```
🔵 Using Windows Hotspot Controller (ACTUAL bandwidth control)
```

If you see this, you're in ACTUAL control mode! 🎉

### Step 4: Connect Devices to Hotspot

1. **On each device:**
   - Go to Wi-Fi settings
   - Connect to your hotspot (e.g., "EqualNet-Hotspot")
   - Enter the password

2. **Verify connections:**
   - Open EqualNet dashboard: http://localhost:5000
   - Check "Clients" tab to see connected devices
   - You should see their IPs (192.168.137.x typically)

### Step 5: Apply Bandwidth Limits

1. **Open EqualNet Dashboard:**
   ```
   http://localhost:5000
   ```

2. **Go to Settings tab:**
   - Check "Bandwidth Control" section
   - Status should show: "✅ Hotspot Active (QoS Ready)"
   - Gateway IP should show your hotspot adapter IP

3. **Apply Limits:**
   - Click "🚀 Apply Limits to Router"
   - This creates **actual Windows QoS policies**
   - Each device gets a dedicated bandwidth limit

4. **Verify policies (PowerShell):**
   ```powershell
   # View all QoS policies
   Get-NetQosPolicy
   
   # Check EqualNet policies only
   Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"}
   ```

## 🔍 Verification & Testing

### Check if QoS is Working

**1. View Active Policies:**
```powershell
Get-NetQosPolicy | Format-Table Name, ThrottleRate, IPDstPrefix
```

**2. Expected output:**
```
Name                    ThrottleRate        IPDstPrefix
----                    ------------        -----------
EqualNet_192.168.137.2  26214400           192.168.137.2/32
EqualNet_192.168.137.3  20971520           192.168.137.3/32
```

**3. Test bandwidth on device:**
- Run speed test: https://fast.com or https://speedtest.net
- Speed should be limited to allocated bandwidth
- Try P1 device (should get more) vs P4 device (should get less)

### Monitor QoS in Real-Time

**Dashboard method:**
- Settings → Bandwidth Control
- Shows mode, status, and policies

**PowerShell method:**
```powershell
# Watch policies in real-time
while ($true) {
    Clear-Host
    Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"}
    Start-Sleep -Seconds 2
}
```

## 🛠️ Troubleshooting

### ❌ "Need Admin Rights" Error

**Problem:** EqualNet running without administrator privileges

**Solution:**
```powershell
# Stop current instance (Ctrl+C)
# Restart with admin
Start-Process python -ArgumentList "api_server.py" -Verb RunAs
```

### ❌ Hotspot Not Detected

**Problem:** Windows hotspot not enabled or network adapter issue

**Solution:**
```powershell
# Check network adapters
Get-NetAdapter

# Look for adapter with "Local Area Connection*" or similar
# Enable hotspot in Windows Settings

# Restart network adapters
Restart-NetAdapter -Name "Wi-Fi"
```

### ❌ Policies Not Applying

**Problem:** QoS policies created but not enforcing

**Solution:**
```powershell
# Clear all EqualNet policies
Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"} | Remove-NetQosPolicy -Confirm:$false

# Restart EqualNet server
# Re-apply limits from dashboard
```

### ❌ Devices Can't Connect to Hotspot

**Problem:** Firewall blocking hotspot connections

**Solution:**
```powershell
# Allow hotspot through firewall
Set-NetFirewallProfile -Profile Public, Private -Enabled True

# Or temporarily disable firewall (NOT recommended for production)
Set-NetFirewallProfile -Profile Domain, Public, Private -Enabled False
```

### ⚠️ Bandwidth Limits Not Accurate

**Problem:** Speed tests show different speeds than configured

**Possible causes:**
1. **QoS not supported by network adapter**
   - Check: `Get-NetAdapterAdvancedProperty -Name "Wi-Fi" -DisplayName "*QoS*"`
   - Some adapters don't support QoS

2. **Other traffic on network**
   - QoS applies per-device, not total
   - Multiple devices share upstream bandwidth

3. **TCP overhead**
   - Actual speed = limit × 0.85-0.95 (due to protocol overhead)

## 📊 Performance Tips

### Optimize QoS Performance

**1. Use appropriate bandwidth limits:**
```python
# In EqualNet, set realistic limits
# Example for 100 Mbps total:
# P1 devices: 40-50 Mbps
# P2 devices: 25-30 Mbps
# P3 devices: 15-20 Mbps
# P4 devices: 10-15 Mbps
```

**2. Limit number of connected devices:**
- QoS works best with 5-10 devices
- More devices = more overhead
- Consider upgrading to dedicated router for 15+ devices

**3. Monitor system resources:**
```powershell
# Check CPU/Network usage
Get-Counter '\Processor(_Total)\% Processor Time'
Get-Counter '\Network Interface(*)\Bytes Total/sec'
```

### Hotspot Best Practices

1. **Keep laptop plugged in** - Hotspot drains battery
2. **Use wired internet** - Better performance than Wi-Fi relay
3. **Position laptop centrally** - Better signal for all devices
4. **Update Wi-Fi drivers** - Latest drivers = better QoS support
5. **Disable power saving** - Prevents hotspot disconnections

## 🔄 Switching Between Modes

### Router Mode → Hotspot Mode

1. Edit `api_server.py`:
   ```python
   HOTSPOT_MODE = True  # Change to True
   ```

2. Restart server as admin
3. Enable Windows hotspot
4. Connect devices to hotspot
5. Apply limits from dashboard

### Hotspot Mode → Router Mode

1. Edit `api_server.py`:
   ```python
   HOTSPOT_MODE = False  # Change to False
   ```

2. Clear existing QoS policies:
   ```powershell
   Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"} | Remove-NetQosPolicy -Confirm:$false
   ```

3. Disable Windows hotspot
4. Connect laptop to router's network
5. Restart server (no admin needed)

## 📝 Technical Details

### Windows QoS Architecture

```
Application Layer (EqualNet)
        ↓
PowerShell NetQoS Commands
        ↓
Windows QoS Packet Scheduler (pacer.sys)
        ↓
Network Driver (NDIS)
        ↓
Physical Network Adapter
```

### QoS Policy Components

Each policy created by EqualNet contains:
- **Name:** `EqualNet_{IP_ADDRESS}_{Direction}`
- **IP Filter:** Destination IP (download) or Source IP (upload)
- **Throttle Rate:** Bits per second limit
- **DSCP Value:** Priority marking (optional)

Example policy:
```powershell
Name: EqualNet_192.168.137.2_Download
IPDstPrefix: 192.168.137.2/32
ThrottleRateActionBitsPerSecond: 26214400  # 25 Mbps
DSCPAction: 46  # EF (Expedited Forwarding) for P1
```

### DSCP Priority Mapping

| Priority | DSCP Value | Traffic Class | EqualNet Use |
|----------|-----------|---------------|--------------|
| P1       | 46 (EF)   | Expedited Forwarding | Critical devices |
| P2       | 34 (AF41) | Assured Forwarding 4 | High priority |
| P3       | 26 (AF31) | Assured Forwarding 3 | Normal |
| P4       | 18 (AF21) | Assured Forwarding 2 | Low priority |

## 🎓 Additional Resources

### Windows QoS Documentation
- [Microsoft: QoS Policy](https://docs.microsoft.com/en-us/windows-server/networking/technologies/qos/qos-policy-top)
- [NetQosPolicy Cmdlets](https://docs.microsoft.com/en-us/powershell/module/netqos)

### Mobile Hotspot Help
- [Windows 10: Mobile Hotspot](https://support.microsoft.com/en-us/windows/use-your-windows-pc-as-a-mobile-hotspot-c89b0fad-72d5-41e8-f7ea-406ad9036b85)

### Network Troubleshooting
```powershell
# Comprehensive network check
ipconfig /all
netsh wlan show hostednetwork
netsh interface show interface
Get-NetAdapter | Format-Table
Get-NetQosPolicy | Format-Table
```

## 🎉 Success Checklist

- [ ] Windows hotspot enabled and broadcasting
- [ ] EqualNet running as administrator
- [ ] HOTSPOT_MODE = True in api_server.py
- [ ] Dashboard shows "✅ Hotspot Active (QoS Ready)"
- [ ] Devices connected to hotspot
- [ ] QoS policies visible: `Get-NetQosPolicy`
- [ ] Speed tests show limited bandwidth
- [ ] Different priorities get different speeds

When all boxes are checked, you have **ACTUAL bandwidth control**! 🚀

---

**Need help?** Check the logs in EqualNet terminal or run diagnostics:
```powershell
# Full diagnostic
python -c "from windows_hotspot_controller import WindowsHotspotController; c = WindowsHotspotController(); print(c.get_info())"
```
