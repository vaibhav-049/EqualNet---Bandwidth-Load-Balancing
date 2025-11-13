from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import threading
import time
import csv
import io
from datetime import datetime, timedelta
from monitor import get_connected_devices
from load_balancer import LoadBalancer
from utils import get_bandwidth_usage
from device_recognizer import DeviceRecognizer
from analytics_db import AnalyticsDB
from alert_system import AlertManager
from qos_manager import QoSManager
from network_scanner import get_all_network_devices
from router_controller import RouterController
from windows_hotspot_controller import WindowsHotspotController

HOTSPOT_MODE = True

app = Flask(__name__, static_folder='static')
CORS(app)

device_recognizer = DeviceRecognizer()
analytics_db = AnalyticsDB()
alert_manager = AlertManager()
qos_manager = QoSManager()

if HOTSPOT_MODE:
    bandwidth_controller = WindowsHotspotController()
    print("🔵 Using Windows Hotspot Controller (ACTUAL bandwidth control)")
else:
    bandwidth_controller = RouterController()
    print("🟡 Using Router Controller (simulation mode)")

print("🔄 Loading saved device names from database...")
try:
    saved_devices = analytics_db.get_all_clients()
    for device in saved_devices:
        ip = device.get('ip_address')
        name = device.get('friendly_name')
        if ip and name:
            device_recognizer.set_custom_name(ip, name)
    print(f"✅ Loaded {len([d for d in saved_devices if d.get('friendly_name')])} custom device names")
except Exception as e:
    print(f"⚠️ Could not load device names: {e}")

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
    "device_info": {},
    "known_devices": set(),
    "qos_enabled": True,
    "app_types": {},
    "priority_adjustments": {}
}

lb = None


def update_loop():
    global lb, STATE
    iteration = 0
    last_full_scan = 0
    db_names_cache = {}
    last_db_load = 0
    
    while True:
        try:
            current_time = time.time()
            
            if current_time - last_db_load > 30:
                db_devices = analytics_db.get_all_clients()
                db_names_cache = {
                    d['ip_address']: d.get('friendly_name')
                    for d in db_devices if d.get('friendly_name')
                }
                last_db_load = current_time
            
            if current_time - last_full_scan > 300:
                clients = get_all_network_devices()
                last_full_scan = current_time
            else:
                clients = get_connected_devices()
            
            if HOTSPOT_MODE:
                clients = [ip for ip in clients if ip.startswith('192.168.137.')]
            
            for ip in clients:
                device_info = device_recognizer.get_device_info(ip)
                
                if ip in db_names_cache:
                    device_info['friendly_name'] = db_names_cache[ip]
                    device_recognizer.set_custom_name(ip, db_names_cache[ip])
                
                STATE["device_info"][ip] = device_info
                
                if ip not in STATE["known_devices"]:
                    STATE["known_devices"].add(ip)
                    alert_manager.check_new_device(
                        ip,
                        device_info["mac"],
                        device_info
                    )
                    analytics_db.update_client_metadata(
                        ip,
                        device_info["mac"],
                        device_info["vendor"],
                        device_info["device_type"],
                        device_info["friendly_name"]
                    )
            
            STATE["clients"] = clients[:20]
            
            if not STATE["priorities"]:
                for i, ip in enumerate(clients):
                    priority = min(i + 1, STATE["max_priority"])
                    STATE["priorities"][ip] = priority
            
            if STATE["qos_enabled"] and iteration % 5 == 0:
                client_data = []
                for ip in clients:
                    client_data.append({
                        "ip": ip,
                        "usage": lb.usage.get(ip, 0) if lb else 0,
                        "upload": STATE["network_stats"]["sent"] / len(clients),
                        "download": STATE["network_stats"]["recv"] / len(clients)
                    })
                
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
            
            analytics_db.log_bandwidth(sent, recv, len(clients))
            
            client_list = []
            for ip in clients:
                usage = STATE["usage"].get(ip, 0)
                allocated = STATE["allocations"].get(ip, 0)
                priority = STATE["priorities"].get(ip, 1)
                device_info = STATE["device_info"].get(ip, {})
                
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
                
                if allocated > 0:
                    usage_percent = (usage / allocated) * 100
                    device_name = device_info.get("friendly_name", ip)
                    
                    alert_manager.check_bandwidth_limit(
                        usage,
                        allocated,
                        ip,
                        device_name
                    )
                    
                    alert_manager.check_sustained_high_usage(
                        ip,
                        usage_percent,
                        device_name
                    )
                    
                    if usage_percent >= 95:
                        alert_manager.check_critical_usage(
                            ip,
                            usage_percent,
                            device_name
                        )
                
                client_list.append({
                    "ip": ip,
                    "priority": priority,
                    "usage": usage,
                    "allocated": allocated
                })
            
            if len(client_list) > 1 and iteration > 30:
                high_priority = [c for c in client_list if c['priority'] <= 2]
                low_priority = [c for c in client_list if c['priority'] >= 4]
                
                if high_priority and low_priority:
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
    return send_from_directory('static', 'index.html')


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


@app.route('/api/device/<ip>/label', methods=['GET', 'POST'])
def device_label(ip):
    """Get or set custom device label/name"""
    if request.method == 'POST':
        data = request.json
        if data and "label" in data:
            custom_label = data["label"].strip()
            
            # Update in device recognizer (in-memory)
            device_recognizer.set_custom_name(ip, custom_label)
            
            # Update in database for persistence
            device_info = STATE["device_info"].get(ip, {})
            analytics_db.update_client_metadata(
                ip,
                device_info.get("mac", ""),
                device_info.get("vendor", ""),
                device_info.get("device_type", ""),
                custom_label
            )
            
            if ip in STATE["device_info"]:
                STATE["device_info"][ip]["friendly_name"] = custom_label
            else:
                STATE["device_info"][ip] = {
                    "friendly_name": custom_label,
                    "ip": ip
                }
            
            updated_info = device_recognizer.get_device_info(ip)
            STATE["device_info"][ip] = updated_info
            
            return jsonify({
                "success": True,
                "ip": ip,
                "label": custom_label,
                "message": f"Device renamed to '{custom_label}'"
            })
        return jsonify({"success": False, "error": "Label not provided"})
    else:
        device_info = STATE["device_info"].get(ip, {})
        return jsonify({
            "ip": ip,
            "label": device_info.get("friendly_name", ip)
        })


@app.route('/api/alerts/high-usage')
def get_high_usage_alerts():
    all_alerts = alert_manager.get_recent_alerts(100)
    high_usage_alerts = [
        alert for alert in all_alerts
        if alert["type"] in ["bandwidth_limit", "unusual_traffic"]
    ]
    for alert in high_usage_alerts:
        alert["timestamp"] = alert["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(high_usage_alerts)


@app.route('/api/router/info')
def router_info():
    """Get bandwidth controller information"""
    info = bandwidth_controller.get_info()
    info['mode'] = 'hotspot' if HOTSPOT_MODE else 'router'
    return jsonify(info)


@app.route('/api/router/apply_limits', methods=['POST'])
def apply_limits_to_router():
    """Apply calculated bandwidth limits to network controller"""
    try:
        results = bandwidth_controller.apply_all_limits(
            STATE["allocations"], STATE.get("priorities", {})
        )
        success_count = sum(1 for v in results.values() if v)
        
        return jsonify({
            "success": True,
            "applied": success_count,
            "total": len(STATE["allocations"]),
            "results": results,
            "message": f"Applied limits to {success_count}/{len(STATE['allocations'])} devices"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/router/set_limit/<ip>', methods=['POST'])
def set_single_limit(ip):
    """Set bandwidth limit for single device"""
    data = request.get_json()
    download = data.get('download', 25)
    upload = data.get('upload', 10)
    
    try:
        success = bandwidth_controller.set_bandwidth_limit(
            ip, download, upload
        )
        return jsonify({
            "success": success,
            "ip": ip,
            "download": download,
            "upload": upload
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/router/set_priority/<ip>', methods=['POST'])
def apply_priority_to_router(ip):
    """Apply priority to router QoS"""
    data = request.get_json()
    priority = data.get('priority', 4)
    
    STATE["priorities"][ip] = priority
    
    try:
        success = bandwidth_controller.set_priority(ip, priority)
        return jsonify({
            "success": success,
            "ip": ip,
            "priority": priority,
            "message": f"Priority P{priority} applied to router"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/router/clear_limits', methods=['POST'])
def clear_router_limits():
    """Clear all bandwidth limits from controller"""
    try:
        success = bandwidth_controller.clear_all_limits()
        return jsonify({
            "success": success,
            "message": "All limits cleared from router"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/alerts/threshold', methods=['POST'])
def set_usage_threshold():
    """Set custom threshold for high usage alerts"""
    data = request.json
    if data and "threshold" in data:
        threshold = float(data["threshold"])
        if 0 < threshold <= 100:
            alert_manager.set_threshold("bandwidth_limit", threshold)
            return jsonify({
                "success": True,
                "threshold": threshold,
                "message": f"High usage threshold set to {threshold}%"
            })
    return jsonify({"success": False, "error": "Invalid threshold"})


@app.route('/api/export/csv/bandwidth')
def export_bandwidth_csv():
    """Export bandwidth history to CSV"""
    hours = request.args.get('hours', 24, type=int)
    data = analytics_db.get_bandwidth_history(hours)
    
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    response = Response(output.getvalue(), mimetype='text/csv')
    filename = f'bandwidth_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/api/export/csv/clients')
def export_clients_csv():
    """Export client usage data to CSV"""
    hours = request.args.get('hours', 24, type=int)
    
    # Get all unique clients from recent history
    since = datetime.now() - timedelta(hours=hours)
    conn = analytics_db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT
            ip_address,
            mac_address,
            vendor,
            device_type,
            AVG(priority) as avg_priority,
            AVG(allocated_bandwidth) as avg_allocated,
            AVG(used_bandwidth) as avg_used,
            AVG(upload_speed) as avg_upload,
            AVG(download_speed) as avg_download,
            MAX(used_bandwidth) as peak_usage,
            COUNT(*) as data_points
        FROM client_history
        WHERE timestamp >= ?
        GROUP BY ip_address
        ORDER BY avg_used DESC
    ''', (since,))
    
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    if rows:
        fieldnames = ['ip_address', 'mac_address', 'vendor', 'device_type',
                     'avg_priority', 'avg_allocated', 'avg_used', 'avg_upload',
                     'avg_download', 'peak_usage', 'data_points']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    
    response = Response(output.getvalue(), mimetype='text/csv')
    filename = f'client_usage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/api/export/csv/alerts')
def export_alerts_csv():
    """Export alerts history to CSV"""
    limit = request.args.get('limit', 1000, type=int)
    
    conn = analytics_db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT
            timestamp,
            alert_type,
            ip_address,
            message,
            severity
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    if rows:
        fieldnames = ['timestamp', 'alert_type', 'ip_address', 'message', 'severity']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    
    response = Response(output.getvalue(), mimetype='text/csv')
    filename = f'alerts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@app.route('/api/export/csv/full-report')
def export_full_report():
    """Export comprehensive report with all data"""
    hours = request.args.get('hours', 24, type=int)
    
    # Get daily report summary
    report = analytics_db.get_daily_report(hours // 24 or 1)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['EqualNet Analytics Report'])
    writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([f'Period: Last {hours} hours'])
    writer.writerow([])
    
    # Summary section
    writer.writerow(['=== SUMMARY ==='])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Unique Clients', report.get('unique_clients', 0)])
    writer.writerow(['Average Bandwidth (Mbps)', report.get('avg_bandwidth', 0)])
    writer.writerow(['Peak Bandwidth (Mbps)', report.get('peak_bandwidth', 0)])
    writer.writerow(['Peak Hour', report.get('peak_hour', 'N/A')])
    writer.writerow([])
    
    # Top clients section
    writer.writerow(['=== TOP BANDWIDTH CONSUMERS ==='])
    top_clients = analytics_db.get_top_clients(10, hours)
    if top_clients:
        writer.writerow(['IP Address', 'Avg Usage', 'Total Usage', 'Sessions'])
        for client in top_clients:
            writer.writerow([
                client['ip_address'],
                f"{client['avg_usage']:.2f}",
                f"{client['total_usage']:.2f}",
                client['sessions']
            ])
    writer.writerow([])
    
    # Recent alerts section
    writer.writerow(['=== RECENT ALERTS ==='])
    alerts = alert_manager.get_recent_alerts(20)
    if alerts:
        writer.writerow(['Timestamp', 'Type', 'IP', 'Severity', 'Message'])
        for alert in alerts:
            writer.writerow([
                alert['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                alert['type'],
                alert.get('data', {}).get('ip', 'N/A'),
                alert['severity'],
                alert['message']
            ])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    filename = f'full_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


if __name__ == '__main__':
    print("🚀 EqualNet API Server Starting...")
    print("📡 API: http://localhost:5000")
    print("🌐 Dashboard: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
