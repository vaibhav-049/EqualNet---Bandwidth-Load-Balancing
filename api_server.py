from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
import time
from monitor import get_connected_devices
from load_balancer import LoadBalancer
from utils import get_bandwidth_usage
from device_recognizer import DeviceRecognizer
from analytics_db import AnalyticsDB
from alert_system import AlertManager
from qos_manager import QoSManager
from network_scanner import get_all_network_devices

app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize new modules
device_recognizer = DeviceRecognizer()
analytics_db = AnalyticsDB()
alert_manager = AlertManager()
qos_manager = QoSManager()

STATE = {
    "total_bandwidth": 100,
    "max_priority": 5,
    "min_bandwidth_percent": 10,
    "clients": [],
    "priorities": {},
    "allocations": {},
    "usage": {},
    "network_stats": {"sent": 0, "recv": 0},
    "history": {
        "time": [],
        "upload": [],
        "download": []
    },
    "device_info": {},  # Device recognition data
    "known_devices": set(),  # Track seen devices
    "qos_enabled": True,  # QoS auto-adjustment enabled
    "app_types": {},  # Detected application types
    "priority_adjustments": {}  # Dynamic priority changes
}

lb = None


def update_loop():
    global lb, STATE
    iteration = 0
    last_full_scan = 0
    
    while True:
        try:
            # Use full network scan every 5 minutes, else use ARP
            current_time = time.time()
            if current_time - last_full_scan > 300:  # 5 minutes
                print("🔍 [SCAN] Running full network scan...")
                clients = get_all_network_devices()
                last_full_scan = current_time
            else:
                clients = get_connected_devices()
            
            # Device recognition and new device detection
            # IMPORTANT: Update device_info BEFORE setting STATE["clients"]
            for ip in clients:
                device_info = device_recognizer.get_device_info(ip)
                STATE["device_info"][ip] = device_info
                
                # Debug: Log vendor detection
                if iteration == 0 or ip not in STATE.get("logged_devices", set()):
                    print(f"🔍 [DEBUG] {ip}: MAC={device_info['mac']}, "
                          f"Vendor={device_info['vendor']}, "
                          f"Type={device_info['device_type']}")
                    if "logged_devices" not in STATE:
                        STATE["logged_devices"] = set()
                    STATE["logged_devices"].add(ip)
            
                
                # Check for new devices
                if ip not in STATE["known_devices"]:
                    STATE["known_devices"].add(ip)
                    alert_manager.check_new_device(
                        ip,
                        device_info["mac"],
                        device_info
                    )
                    # Log to database
                    analytics_db.update_client_metadata(
                        ip,
                        device_info["mac"],
                        device_info["vendor"],
                        device_info["device_type"],
                        device_info["friendly_name"]
                    )
            
            # Update clients list AFTER device_info is populated
            STATE["clients"] = clients[:20]
            
            # Initialize priorities for new clients
            if not STATE["priorities"]:
                for i, ip in enumerate(clients):
                    # Assign priority (1 = highest, max_priority = lowest)
                    priority = min(i + 1, STATE["max_priority"])
                    STATE["priorities"][ip] = priority
            
            # QoS Dynamic Priority Adjustment
            if STATE["qos_enabled"] and iteration % 30 == 0:  # Every 60 seconds
                client_data = []
                for ip in clients:
                    client_data.append({
                        "ip": ip,
                        "usage": lb.usage.get(ip, 0) if lb else 0,
                        "upload": STATE["network_stats"]["sent"] / len(clients),
                        "download": STATE["network_stats"]["recv"] / len(clients)
                    })
                
                # Optimize priorities using QoS
                optimized = qos_manager.optimize_priorities(client_data)
                for ip, info in optimized.items():
                    old_priority = STATE["priorities"].get(ip, 4)
                    new_priority = info["priority"]
                    
                    if old_priority != new_priority:
                        STATE["priorities"][ip] = new_priority
                        STATE["app_types"][ip] = info["app_type"]
                        STATE["priority_adjustments"][ip] = {
                            "old": old_priority,
                            "new": new_priority,
                            "reason": info["app_type"]
                        }
                        print(f"🎯 [QoS] {ip}: Priority {old_priority}→{new_priority} "
                              f"({info['app_type']})")
            
            lb = LoadBalancer(
                STATE["total_bandwidth"],
                max_priority=STATE["max_priority"],
                min_bandwidth_percent=STATE["min_bandwidth_percent"]
            )
            lb.register_clients(clients, STATE["priorities"])
            
            allocations = lb.rebalance_load()
            STATE["allocations"] = allocations
            STATE["usage"] = lb.usage
            
            sent, recv = get_bandwidth_usage()
            STATE["network_stats"] = {
                "sent": round(sent, 2),
                "recv": round(recv, 2)
            }
            
            # Log bandwidth to database
            analytics_db.log_bandwidth(sent, recv, len(clients))
            
            # Log client usage and check alerts
            client_list = []
            for ip in clients:
                usage = STATE["usage"].get(ip, 0)
                allocated = STATE["allocations"].get(ip, 0)
                priority = STATE["priorities"].get(ip, 1)
                device_info = STATE["device_info"].get(ip, {})
                
                # Log to database
                analytics_db.log_client_usage({
                    "ip": ip,
                    "mac": device_info.get("mac", ""),
                    "vendor": device_info.get("vendor", ""),
                    "device_type": device_info.get("device_type", ""),
                    "priority": priority,
                    "allocated": allocated,
                    "usage": usage,
                    "upload": sent / len(clients) if clients else 0,
                    "download": recv / len(clients) if clients else 0
                })
                
                # Check bandwidth limit
                if allocated > 0:
                    alert_manager.check_bandwidth_limit(
                        usage,
                        allocated,
                        ip,
                        device_info.get("friendly_name", ip)
                    )
                
                client_list.append({
                    "ip": ip,
                    "priority": priority,
                    "usage": usage,
                    "allocated": allocated
                })
            
            # Check priority starvation (only if priorities are stable)
            # Skip check for first minute or when QoS just adjusted priorities
            if len(client_list) > 1 and iteration > 30:
                # Only alert if priority difference is significant (>2 levels)
                # and not caused by QoS auto-adjustment
                high_priority_clients = [c for c in client_list if c['priority'] <= 2]
                low_priority_clients = [c for c in client_list if c['priority'] >= 4]
                
                if high_priority_clients and low_priority_clients:
                    alert_manager.check_priority_starvation(client_list)
            
            iteration += 1
            STATE["history"]["time"].append(iteration)
            STATE["history"]["upload"].append(sent)
            STATE["history"]["download"].append(recv)
            
            if len(STATE["history"]["time"]) > 30:
                STATE["history"]["time"] = (
                    STATE["history"]["time"][-30:]
                )
                STATE["history"]["upload"] = (
                    STATE["history"]["upload"][-30:]
                )
                STATE["history"]["download"] = (
                    STATE["history"]["download"][-30:]
                )
            
            msg = (
                f"✓ Updated: {len(clients)} clients, "
                f"{sent:.2f} KB/s up, {recv:.2f} KB/s down"
            )
            print(msg)
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error in update loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


thread = threading.Thread(target=update_loop, daemon=True)
thread.start()


@app.route('/')
def index():
    return send_from_directory('static', 'index_pro.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/api/status')
def get_status():
    total_alloc = round(
        sum(STATE["allocations"].values()), 2
    ) if STATE["allocations"] else 0
    
    return jsonify({
        "total_bandwidth": STATE["total_bandwidth"],
        "max_priority": STATE["max_priority"],
        "min_bandwidth_percent": STATE["min_bandwidth_percent"],
        "total_clients": len(STATE["clients"]),
        "network_stats": STATE["network_stats"],
        "total_allocated": total_alloc
    })


@app.route('/api/clients')
def get_clients():
    clients_data = []
    for ip in STATE["clients"]:
        usage = STATE["usage"].get(ip, 0)
        total_bw = STATE["total_bandwidth"]
        usage_pct = round((usage / total_bw) * 100, 1)
        device_info = STATE["device_info"].get(ip, {})
        
        # Debug: Log device_info
        if not device_info:
            print(f"⚠️ [API] No device_info for {ip}!")
        elif device_info.get("vendor") == "Unknown":
            print(f"⚠️ [API] {ip} has Unknown vendor! "
                  f"MAC={device_info.get('mac')}, "
                  f"device_info keys={list(device_info.keys())}")
        
        clients_data.append({
            "ip": ip,
            "priority": STATE["priorities"].get(ip, 1),
            "usage": round(usage, 2),
            "allocated": round(STATE["allocations"].get(ip, 0), 2),
            "usage_percent": usage_pct,
            "mac": device_info.get("mac", "Unknown"),
            "vendor": device_info.get("vendor", "Unknown"),
            "device_type": device_info.get("device_type", "unknown"),
            "icon": device_info.get("icon", "❓"),
            "friendly_name": device_info.get("friendly_name", ip),
            "app_type": STATE["app_types"].get(ip, "browsing")
        })
    return jsonify(clients_data)


@app.route('/api/history')
def get_history():
    return jsonify(STATE["history"])


@app.route('/api/config', methods=['GET', 'POST'])
def update_config():
    if request.method == 'GET':
        return jsonify({
            "total_bandwidth": STATE["total_bandwidth"],
            "max_priority": STATE["max_priority"],
            "min_bandwidth_percent": STATE["min_bandwidth_percent"]
        })
    
    data = request.json
    if data and "total_bandwidth" in data:
        STATE["total_bandwidth"] = int(data["total_bandwidth"])
    if data and "max_priority" in data:
        STATE["max_priority"] = int(data["max_priority"])
    if data and "min_bandwidth_percent" in data:
        STATE["min_bandwidth_percent"] = int(data["min_bandwidth_percent"])
    if data and "priorities" in data:
        STATE["priorities"].update(data["priorities"])
    return jsonify({"success": True})


@app.route('/api/priority/<ip>', methods=['POST'])
def update_priority(ip):
    data = request.json
    if data:
        priority = int(data.get("priority", 1))
        # Validate priority against max_priority
        if priority < 1:
            priority = 1
        if priority > STATE["max_priority"]:
            priority = STATE["max_priority"]
        STATE["priorities"][ip] = priority
        return jsonify({"success": True, "ip": ip, "priority": priority})
    return jsonify({"success": False})


@app.route('/api/device/<ip>', methods=['GET', 'POST'])
def device_info(ip):
    """Get or update device info"""
    if request.method == 'GET':
        return jsonify(STATE["device_info"].get(ip, {}))
    else:
        data = request.json
        if data and "friendly_name" in data:
            device_recognizer.set_custom_name(ip, data["friendly_name"])
            # Refresh device info
            STATE["device_info"][ip] = device_recognizer.get_device_info(ip)
            return jsonify({"success": True})
        return jsonify({"success": False})


@app.route('/api/analytics/bandwidth/<int:hours>')
def analytics_bandwidth(hours):
    """Get bandwidth history"""
    data = analytics_db.get_bandwidth_history(hours)
    return jsonify(data)


@app.route('/api/analytics/client/<ip>/<int:hours>')
def analytics_client(ip, hours):
    """Get client usage summary"""
    data = analytics_db.get_client_usage_summary(ip, hours)
    return jsonify(data)


@app.route('/api/analytics/top/<int:limit>')
def analytics_top(limit):
    """Get top bandwidth consumers"""
    data = analytics_db.get_top_clients(limit, 24)
    return jsonify(data)


@app.route('/api/analytics/hourly/<int:hours>')
def analytics_hourly(hours):
    """Get hourly statistics"""
    data = analytics_db.get_hourly_stats(hours)
    return jsonify(data)


@app.route('/api/analytics/report/<int:days>')
def analytics_report(days):
    """Get daily report"""
    data = analytics_db.get_daily_report(days)
    return jsonify(data)


@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    alerts = alert_manager.get_recent_alerts(50)
    # Convert datetime to string
    for alert in alerts:
        alert["timestamp"] = alert["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(alerts)


@app.route('/api/alerts/config', methods=['GET', 'POST'])
def alerts_config():
    """Get or update alert configuration"""
    if request.method == 'GET':
        return jsonify(alert_manager.get_thresholds())
    else:
        data = request.json
        if data:
            for key, value in data.items():
                alert_manager.set_threshold(key, value)
            return jsonify({"success": True})
        return jsonify({"success": False})


@app.route('/api/devices/all')
def get_all_devices():
    """Get all known devices from database"""
    devices = analytics_db.get_all_clients()
    return jsonify(devices)


@app.route('/api/qos/status')
def qos_status():
    """Get QoS status and statistics"""
    stats = qos_manager.get_statistics()
    return jsonify({
        "enabled": STATE["qos_enabled"],
        "app_types": STATE["app_types"],
        "priority_adjustments": STATE["priority_adjustments"],
        "statistics": stats
    })


@app.route('/api/qos/toggle', methods=['POST'])
def qos_toggle():
    """Enable/disable QoS"""
    STATE["qos_enabled"] = not STATE["qos_enabled"]
    status = "enabled" if STATE["qos_enabled"] else "disabled"
    print(f"🎯 [QoS] Auto-adjustment {status}")
    return jsonify({
        "success": True,
        "enabled": STATE["qos_enabled"],
        "message": f"QoS {status}"
    })


@app.route('/api/qos/explain/<ip>')
def qos_explain(ip):
    """Get explanation for priority adjustment"""
    explanation = qos_manager.get_priority_explanation(ip)
    app_type = STATE["app_types"].get(ip, "unknown")
    return jsonify({
        "ip": ip,
        "app_type": app_type,
        "explanation": explanation,
        "current_priority": STATE["priorities"].get(ip, 4)
    })


if __name__ == '__main__':
    print("🚀 EqualNet API Server Starting...")
    print("📡 API: http://localhost:5000")
    print("🌐 Dashboard: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
