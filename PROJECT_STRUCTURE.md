# 📁 EqualNet Project Structure - Complete

```
os_pbl/
│
├── 🚀 Core Application Files
│   ├── api_server.py              ⭐ Main Flask server (HOTSPOT_MODE config)
│   ├── equalnet_main.py           📊 CLI monitoring interface
│   ├── monitor.py                 🔍 Network monitoring loop
│   └── utils.py                   🛠️ Helper utilities
│
├── ⚡ Bandwidth Control (NEW!)
│   ├── windows_hotspot_controller.py  🔵 ACTUAL bandwidth control via Windows QoS
│   ├── router_controller.py           🔹 Router API controller (simulation)
│   ├── qos_manager.py                 🎯 QoS priority management
│   └── load_balancer.py               ⚖️ Dynamic bandwidth allocation
│
├── 🌐 Network Discovery
│   ├── network_scanner.py         📡 Subnet scanning & device detection
│   ├── device_recognizer.py       📱 Device type identification (300+ vendors)
│   └── client_detector.py         🔎 Active client detection
│
├── 📊 Analytics & Storage
│   ├── analytics_db.py            🗄️ SQLite database operations
│   ├── alert_system.py            🚨 Bandwidth alerts & notifications
│   └── equalnet.db                💾 Historical data storage
│
├── 🎨 Web Dashboard (Static Files)
│   └── static/
│       ├── index.html             🖥️ Main dashboard UI
│       ├── app.js                 ⚙️ Frontend logic & API calls
│       └── style.css              🎨 Dashboard styling
│
├── 📚 Documentation (NEW!)
│   ├── README.md                  📖 Main documentation (updated)
│   ├── HOTSPOT_SETUP.md           🔧 Complete Windows Hotspot setup guide
│   ├── IMPLEMENTATION_COMPLETE.md 🎉 Feature summary & technical details
│   └── THIS_FILE.md               📁 Project structure overview
│
├── 🚀 Launchers & Tools (NEW!)
│   ├── start_equalnet.bat         🎯 One-click launcher with admin rights
│   ├── diagnostic.py              🔍 System configuration checker
│   └── restart_server.bat         🔄 Server restart script
│
├── ⚙️ Configuration
│   ├── requirements-service.txt   📦 Python dependencies
│   ├── .gitignore                 🚫 Git ignore rules
│   └── .vscode/                   🛠️ VS Code settings
│
└── 🗑️ Cache & Generated
    └── __pycache__/               ⚡ Python bytecode cache
```

---

## 🔥 Key Files for ACTUAL Bandwidth Control

### 1. **windows_hotspot_controller.py** (285 lines) 🔵
The star of the show! This is what makes ACTUAL bandwidth control possible.

**What it does:**
- Checks admin privileges
- Detects Windows hotspot adapter
- Creates PowerShell QoS policies
- Sets bandwidth limits and priorities
- Clears policies on demand

**Key methods:**
```python
check_admin()                      # Verify admin rights
get_hotspot_interface()           # Find hotspot adapter
set_bandwidth_limit(ip, down, up) # Apply ACTUAL limit
set_priority(ip, priority)        # Set DSCP priority
apply_all_limits(allocations)     # Batch apply
clear_all_limits()                # Remove all policies
get_info()                        # Status information
```

**PowerShell commands used:**
```powershell
New-NetQosPolicy         # Create bandwidth limits
Remove-NetQosPolicy      # Delete policies
Get-NetAdapter           # Find network adapters
```

---

### 2. **api_server.py** (805 lines) ⭐
Flask web server with integrated bandwidth control.

**Recent additions:**
- Line 20: `HOTSPOT_MODE = True/False` configuration
- Lines 27-33: Controller selection logic
- Lines 532-615: Bandwidth control API endpoints

**API Endpoints:**
```
GET  /api/router/info              # Controller status
POST /api/router/apply_limits      # Apply all limits
POST /api/router/set_limit/<ip>    # Single device limit
POST /api/router/set_priority/<ip> # Set priority
POST /api/router/clear_limits      # Clear all policies
```

**Dashboard serves at:** `http://localhost:5000`

---

### 3. **HOTSPOT_SETUP.md** (350+ lines) 📖
Complete guide for setting up Windows Hotspot mode.

**Sections:**
1. Overview & How It Works
2. Step-by-step setup instructions
3. Verification & testing methods
4. Troubleshooting common issues
5. Performance tips & best practices
6. Technical details & architecture

**Must-read for:** First-time setup, troubleshooting

---

### 4. **start_equalnet.bat** 🎯
One-click launcher with automatic admin elevation.

**Features:**
- Checks for admin rights
- Verifies Python installation
- Installs dependencies if missing
- Detects HOTSPOT_MODE setting
- Displays configuration info
- Launches server

**Usage:** Right-click → "Run as administrator"

---

### 5. **diagnostic.py** (200 lines) 🔍
System configuration validator.

**Checks:**
- ✅ Admin privileges
- ✅ Python version (3.7+)
- ✅ Windows version (10+)
- ✅ Required packages
- ✅ HOTSPOT_MODE setting
- ✅ Hotspot adapter status
- ✅ Existing QoS policies

**Usage:** `python diagnostic.py`

---

## 🎯 How Everything Connects

### Request Flow (Hotspot Mode)

```
User clicks "Apply Limits" in Dashboard
        ↓
Browser: app.js sends POST to /api/router/apply_limits
        ↓
Server: api_server.py receives request
        ↓
Controller: windows_hotspot_controller.py processes
        ↓
PowerShell: Executes New-NetQosPolicy commands
        ↓
Windows: Creates QoS policies in network stack
        ↓
Network: ACTUAL bandwidth limits applied to devices
        ↓
Response: Success/failure sent back to browser
        ↓
Dashboard: Updates status display
```

### Data Flow

```
Network Scanner → Device Discovery
        ↓
Monitor → Bandwidth Usage Collection
        ↓
Load Balancer → Fair Allocation Calculation
        ↓
QoS Manager → Priority Assignment
        ↓
Windows Hotspot Controller → ACTUAL Enforcement
        ↓
Analytics DB → Historical Storage
        ↓
Dashboard → Real-time Visualization
```

---

## 🔧 Configuration Quick Reference

### Enable ACTUAL Control

**File:** `api_server.py` (Line 20)
```python
HOTSPOT_MODE = True  # ACTUAL control
```

### Adjust Priorities

**File:** `windows_hotspot_controller.py` (Lines 20-24)
```python
self.dscp_map = {
    1: 46,  # P1: Highest priority
    2: 34,  # P2: High
    3: 26,  # P3: Medium
    4: 18   # P4: Low
}
```

### Change Allocation Algorithm

**File:** `load_balancer.py`
```python
# Fair share, priority-weighted, or custom
```

---

## 📊 File Sizes & Line Counts

| File | Lines | Size | Purpose |
|------|-------|------|---------|
| windows_hotspot_controller.py | 285 | ~12 KB | QoS control |
| api_server.py | 805 | ~28 KB | Web server |
| HOTSPOT_SETUP.md | 350+ | ~18 KB | Setup guide |
| IMPLEMENTATION_COMPLETE.md | 400+ | ~22 KB | Summary |
| diagnostic.py | 200 | ~8 KB | System checker |
| router_controller.py | 330 | ~14 KB | Router API |
| device_recognizer.py | 400+ | ~20 KB | Device detection |
| load_balancer.py | 200+ | ~9 KB | Allocation logic |

**Total new code:** ~2000 lines added for ACTUAL control!

---

## 🎓 Learning Path

**Beginner → Understand the system:**
1. Read README.md
2. Read IMPLEMENTATION_COMPLETE.md
3. Run diagnostic.py
4. Browse dashboard

**Intermediate → Set up hotspot mode:**
1. Read HOTSPOT_SETUP.md
2. Enable Windows Hotspot
3. Run start_equalnet.bat as admin
4. Apply limits from dashboard
5. Verify with Get-NetQosPolicy

**Advanced → Customize & extend:**
1. Study windows_hotspot_controller.py
2. Modify DSCP priorities
3. Adjust allocation algorithms
4. Add custom QoS rules
5. Integrate with monitoring tools

---

## 🚀 Quick Commands Cheatsheet

### Start EqualNet
```powershell
# Easy way
.\start_equalnet.bat  # Right-click → Run as administrator

# Manual way
Start-Process python -ArgumentList "api_server.py" -Verb RunAs
```

### Check Status
```powershell
# System diagnostic
python diagnostic.py

# View QoS policies
Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"}

# Check controller info
python -c "from windows_hotspot_controller import WindowsHotspotController; print(WindowsHotspotController().get_info())"
```

### Manage QoS
```powershell
# View all policies
Get-NetQosPolicy | Format-Table

# Clear EqualNet policies
Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"} | Remove-NetQosPolicy -Confirm:$false

# Check hotspot adapter
Get-NetAdapter | Where-Object {$_.Status -eq "Up"}
```

### Troubleshooting
```powershell
# Check if running as admin
net session

# Restart network adapter
Restart-NetAdapter -Name "Wi-Fi"

# View detailed policy info
Get-NetQosPolicy -Name "EqualNet_*" | Format-List
```

---

## 🎉 Success Indicators

Your system is working perfectly when you see:

**1. Terminal output:**
```
🔵 Using Windows Hotspot Controller (ACTUAL bandwidth control)
✅ Admin rights verified
✅ Hotspot adapter detected: Local Area Connection* 15
```

**2. Dashboard status:**
```
✅ Hotspot Active (QoS Ready)
Mode: hotspot
Controller: WindowsHotspotController
```

**3. PowerShell verification:**
```powershell
PS> Get-NetQosPolicy | Where-Object {$_.Name -like "EqualNet_*"}

Name                          ThrottleRate
----                          ------------
EqualNet_192.168.137.2_Down   26214400
EqualNet_192.168.137.3_Down   20971520
```

**4. Speed test confirmation:**
- Device speeds match allocated bandwidth
- P1 devices faster than P4 devices
- Limits enforced consistently

---

## 📚 Documentation Files Explained

### README.md
- **Audience:** First-time users
- **Content:** Quick start, features overview
- **Length:** ~100 lines
- **Read first:** Yes

### HOTSPOT_SETUP.md
- **Audience:** Users setting up ACTUAL control
- **Content:** Step-by-step guide, troubleshooting
- **Length:** 350+ lines
- **Read when:** Setting up hotspot mode

### IMPLEMENTATION_COMPLETE.md
- **Audience:** Developers, curious users
- **Content:** Technical details, architecture
- **Length:** 400+ lines
- **Read when:** Want to understand how it works

### THIS_FILE.md (PROJECT_STRUCTURE.md)
- **Audience:** Anyone exploring the codebase
- **Content:** File organization, quick reference
- **Length:** This document
- **Read when:** Need to find specific files/code

---

## 🔮 Future Development Ideas

**Short-term:**
- [ ] Web UI for manual policy editing
- [ ] Save/load QoS profiles
- [ ] Real-time bandwidth graphs per device
- [ ] Email/SMS alerts for violations

**Medium-term:**
- [ ] Application-aware QoS (per-app limits)
- [ ] Time-based schedules (different limits by hour)
- [ ] Traffic shaping curves (burst allowance)
- [ ] Multi-gateway support

**Long-term:**
- [ ] Machine learning for usage prediction
- [ ] Mobile app for remote management
- [ ] Integration with router firmware (OpenWrt)
- [ ] Enterprise features (VLAN support, etc.)

---

## 🙏 Credits & Technologies

**Core Technologies:**
- Python 3.13 - Application logic
- Flask - Web framework
- Windows NetQoS - Bandwidth control
- PowerShell - System automation
- Chart.js - Dashboard visualizations
- SQLite - Data storage

**Network Tools:**
- psutil - Network statistics
- scapy - Packet inspection
- ARP - Device discovery

**Frontend:**
- HTML5 + CSS3 - Dashboard UI
- Vanilla JavaScript - No frameworks
- Responsive design - Mobile-friendly

---

**Created:** 2024  
**Version:** 2.0 (Hotspot Mode)  
**Status:** ✅ Production Ready  
**Control:** 🔵 ACTUAL bandwidth limiting enabled!
