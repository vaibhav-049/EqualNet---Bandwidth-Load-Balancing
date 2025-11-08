# 🌐 EqualNet - Intelligent Bandwidth Load Balancing

**EqualNet** is an advanced bandwidth management system with **dynamic QoS**, **device recognition**, **real-time monitoring**, and **intelligent traffic prioritization**. Built with Python and Flask, it provides a beautiful web dashboard for managing network bandwidth across multiple devices.

## ✨ Key Features

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

Quick run (Windows PowerShell)

1. (Optional) Create a virtual environment:

   python -m venv .venv

2. Activate the venv in PowerShell (you may need to change execution policy):

   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; .\.venv\Scripts\Activate.ps1

3. Install dependencies:

   python -m pip install --upgrade pip; python -m pip install -r requirements-service.txt

4. Start the API dashboard (runs update loop in background):

   python api_server.py

   Dashboard: http://localhost:5000

5. Run the CLI monitor (optional):

   python equalnet_main.py

Notes and platform limitations
- The controller (`controller_service.py`) uses Linux `tc` via `tc_controller.py` and network-detection utilities that may not work on Windows. On Windows `controller_service.py` will run but likely detect 0 clients.
- PowerShell may prevent script activation for venv; use `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` to allow running `Activate.ps1`.
- The Flask server started here is for development only. For production, use a WSGI server.

Troubleshooting
- If the API server prints errors in the update loop, check that `psutil` is installed and that `arp`/`ping` are available.

Contact
- If you want I can adapt `client_detector` and `tc_controller` to be cross-platform or Dockerize the Linux parts for development on Windows.
