# 🌐 EqualNet - Intelligent Bandwidth Load Balancing

**EqualNet** is an advanced bandwidth management system with **dynamic QoS**, **device recognition**, **real-time monitoring**, and **ACTUAL bandwidth control** on Windows. Built with Python and Flask, it provides a beautiful web dashboard for managing network bandwidth across multiple devices.

## 🎯 Two Control Modes

### 🔵 Hotspot Mode (ACTUAL Control) ⭐ RECOMMENDED
- **Real bandwidth limiting** using Windows QoS policies
- Your laptop becomes network gateway
- Requires: Windows 10+, Admin rights, Mobile Hotspot enabled
- [📖 Full Setup Guide](HOTSPOT_SETUP.md)

### 🔹 Router Mode (Simulation)
- Calculates bandwidth allocations but doesn't enforce them
- Requires router API access (limited compatibility)
- Good for monitoring and planning

## ✨ Key Features

- ⚡ **ACTUAL Bandwidth Control** - Windows QoS policies for real traffic shaping (Hotspot mode)
- 🎯 **Dynamic QoS & Priority Management** - Automatic application detection (VoIP, Gaming, Streaming, Downloads)
- 📱 **Smart Device Recognition** - 300+ MAC vendor database with device type detection
- 📊 **Real-time Dashboard** - Beautiful Chart.js visualizations with live updates
- 🗄️ **Historical Analytics** - SQLite database for usage trends and reports
- 🚨 **Alert System** - Intelligent notifications for bandwidth issues
- 🔍 **Network Scanner** - Full subnet scanning to detect all connected devices
- 🔒 **Privacy-Aware** - Detects and handles randomized MAC addresses

## 🚀 Technologies Used

- **Backend**: Python 3.13, Flask, SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js
- **Network**: psutil, ARP scanning, subnet discovery
- **Database**: SQLite with analytics module

Prerequisites
- Python 3.10+ installed (detected on this machine: Python 3.13)

## 🚀 Quick Start

### Option 1: Easy Launch (Recommended)

**For ACTUAL bandwidth control:**

1. **Enable Windows Mobile Hotspot:**
   - Settings → Network & Internet → Mobile hotspot
   - Turn on "Share my Internet connection"
   - Set network name and password

2. **Run EqualNet as Administrator:**
   ```powershell
   # Right-click start_equalnet.bat → "Run as administrator"
   ```
   Or:
   ```powershell
   Start-Process python -ArgumentList "api_server.py" -Verb RunAs
   ```

3. **Connect devices to your hotspot**

4. **Open dashboard and apply limits:**
   - http://localhost:5000
   - Settings tab → "Apply Limits to Router"

**Success indicators:**
- ✅ Status: "Hotspot Active (QoS Ready)"
- 🔵 Mode: "hotspot" (ACTUAL control)
- PowerShell test: `Get-NetQosPolicy` shows EqualNet policies

### Option 2: Manual Setup

1. **Install dependencies:**
   ```powershell
   python -m pip install -r requirements-service.txt
   ```

2. **Configure mode (api_server.py line 20):**
   ```python
   HOTSPOT_MODE = True  # True = ACTUAL control, False = simulation
   ```

3. **Run diagnostic:**
   ```powershell
   python diagnostic.py
   ```

4. **Start server:**
   ```powershell
   python api_server.py
   ```

5. **Open dashboard:**
   ```
   http://localhost:5000
   ```

## 📖 Documentation

- [**HOTSPOT_SETUP.md**](HOTSPOT_SETUP.md) - Complete Windows Hotspot setup guide
- [**diagnostic.py**](diagnostic.py) - System configuration checker
- [**start_equalnet.bat**](start_equalnet.bat) - One-click launcher with admin rights

## 🔍 Verification

**Check if QoS is working:**
```powershell
# View active policies
Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"}

# Expected output:
# Name                    ThrottleRate        IPDstPrefix
# EqualNet_192.168.137.2  26214400           192.168.137.2/32
```

**Test bandwidth limits:**
1. Run speed test on device: https://fast.com
2. Speed should match allocated bandwidth
3. Higher priority devices get more bandwidth
- PowerShell may prevent script activation for venv; use `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` to allow running `Activate.ps1`.
- The Flask server started here is for development only. For production, use a WSGI server.

Troubleshooting
- If the API server prints errors in the update loop, check that `psutil` is installed and that `arp`/`ping` are available.

Contact
- If you want I can adapt `client_detector` and `tc_controller` to be cross-platform or Dockerize the Linux parts for development on Windows.
