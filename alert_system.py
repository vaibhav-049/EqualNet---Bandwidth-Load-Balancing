"""
Alert System Module
Manages alerts, notifications, and thresholds
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Callable
import threading


class AlertManager:
    def __init__(self):
        self.alert_handlers = []
        self.thresholds = {
            "bandwidth_limit": 90,  # Alert at 90% usage
            "new_device": True,
            "high_priority_starved": True,
            "unusual_traffic": True,
            "sustained_high_usage": 85,  # Sustained usage threshold
            "critical_usage": 95  # Critical usage threshold
        }
        self.alert_history = []
        self.high_usage_tracker = {}  # Track sustained high usage
        self.email_config = {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": ""
        }
    
    def add_handler(self, handler: Callable):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)
    
    def configure_email(self, smtp_server: str, smtp_port: int,
                       sender: str, password: str, recipient: str):
        """Configure email alerts"""
        self.email_config.update({
            "enabled": True,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "sender_email": sender,
            "sender_password": password,
            "recipient_email": recipient
        })
    
    def send_email(self, subject: str, body: str):
        """Send email alert"""
        if not self.email_config["enabled"]:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config["sender_email"]
            msg['To'] = self.email_config["recipient_email"]
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(
                self.email_config["smtp_server"],
                self.email_config["smtp_port"]
            )
            server.starttls()
            server.login(
                self.email_config["sender_email"],
                self.email_config["sender_password"]
            )
            
            text = msg.as_string()
            server.sendmail(
                self.email_config["sender_email"],
                self.email_config["recipient_email"],
                text
            )
            server.quit()
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def trigger_alert(self, alert_type: str, message: str,
                     severity: str = "info", data: Dict = None):
        """Trigger an alert"""
        alert = {
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(),
            "data": data or {}
        }
        
        self.alert_history.append(alert)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }.get(severity, "📢")
        
        print(f"{emoji} [{severity.upper()}] {message}")
        
        for handler in self.alert_handlers:
            try:
                threading.Thread(
                    target=handler,
                    args=(alert,),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"❌ Alert handler error: {e}")
        
        if severity in ["warning", "error"] and self.email_config["enabled"]:
            subject = f"EqualNet Alert: {alert_type}"
            body = f"""
EqualNet Network Monitor Alert

Type: {alert_type}
Severity: {severity.upper()}
Time: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

Additional Data:
{data}

---
EqualNet Bandwidth Management System
            """.strip()
            
            threading.Thread(
                target=self.send_email,
                args=(subject, body),
                daemon=True
            ).start()
        
        return alert
    
    def check_bandwidth_limit(self, used: float, allocated: float,
                             ip: str, client_name: str = None):
        """Check if bandwidth usage exceeds threshold"""
        if allocated == 0:
            return
        
        usage_percent = (used / allocated) * 100
        
        if usage_percent >= self.thresholds["bandwidth_limit"]:
            name = client_name or ip
            self.trigger_alert(
                "bandwidth_limit",
                f"Client {name} is using {usage_percent:.1f}% of allocated bandwidth",
                severity="warning",
                data={"ip": ip, "used": used, "allocated": allocated}
            )
    
    def check_new_device(self, ip: str, mac: str, device_info: Dict):
        """Alert when new device connects"""
        if self.thresholds["new_device"]:
            vendor = device_info.get("vendor", "Unknown")
            device_type = device_info.get("device_type", "unknown")
            
            self.trigger_alert(
                "new_device",
                f"New device connected: {vendor} {device_type} at {ip}",
                severity="info",
                data={"ip": ip, "mac": mac, "device_info": device_info}
            )
    
    def check_priority_starvation(self, clients: List[Dict]):
        """Check if high priority clients are getting less bandwidth"""
        if not self.thresholds["high_priority_starved"]:
            return
        
        if len(clients) < 2:
            return
        
        sorted_clients = sorted(clients, key=lambda x: x.get("priority", 999))
        
        for i in range(len(sorted_clients) - 1):
            high_pri = sorted_clients[i]
            low_pri = sorted_clients[i + 1]
            
            priority_diff = low_pri.get("priority", 5) - high_pri.get("priority", 1)
            if priority_diff < 2:
                continue
            
            high_usage = high_pri.get("usage", 0)
            low_usage = low_pri.get("usage", 0)
            
            if high_usage > 0.5 and low_usage > high_usage * 2.0:
                self.trigger_alert(
                    "priority_starvation",
                    f"Low priority P{low_pri['priority']} client {low_pri['ip']} "
                    f"using 2x more bandwidth than high priority P{high_pri['priority']} "
                    f"client {high_pri['ip']}",
                    severity="warning",
                    data={
                        "high_priority": high_pri,
                        "low_priority": low_pri,
                        "priority_diff": priority_diff
                    }
                )
    
    def check_unusual_traffic(self, current_usage: float,
                             avg_usage: float, ip: str):
        """Detect unusual traffic patterns"""
        if not self.thresholds["unusual_traffic"]:
            return
        
        if avg_usage == 0:
            return
        
        if current_usage > avg_usage * 3:
            self.trigger_alert(
                "unusual_traffic",
                f"Unusual traffic detected from {ip}: {current_usage:.2f} MB/s (avg: {avg_usage:.2f} MB/s)",
                severity="warning",
                data={"ip": ip, "current": current_usage, "average": avg_usage}
            )
    
    def check_sustained_high_usage(self, ip: str, usage_percent: float,
                                   client_name: str = None):
        """Check for sustained high bandwidth usage"""
        threshold = self.thresholds.get("sustained_high_usage", 85)
        critical_threshold = self.thresholds.get("critical_usage", 95)
        
        if ip not in self.high_usage_tracker:
            self.high_usage_tracker[ip] = {"count": 0, "alerted": False}
        
        if usage_percent >= threshold:
            self.high_usage_tracker[ip]["count"] += 1
            
            if (self.high_usage_tracker[ip]["count"] >= 5 and 
                not self.high_usage_tracker[ip]["alerted"]):
                
                name = client_name or ip
                severity = "error" if usage_percent >= critical_threshold else "warning"
                
                self.trigger_alert(
                    "high_usage",
                    f"Sustained high usage from {name}: {usage_percent:.1f}% for extended period",
                    severity=severity,
                    data={
                        "ip": ip,
                        "usage_percent": usage_percent,
                        "duration_checks": self.high_usage_tracker[ip]["count"]
                    }
                )
                self.high_usage_tracker[ip]["alerted"] = True
        else:
            if ip in self.high_usage_tracker:
                self.high_usage_tracker[ip]["count"] = 0
                self.high_usage_tracker[ip]["alerted"] = False
    
    def check_critical_usage(self, ip: str, usage_percent: float,
                            client_name: str = None):
        """Check for critical bandwidth usage (immediate alert)"""
        critical_threshold = self.thresholds.get("critical_usage", 95)
        
        if usage_percent >= critical_threshold:
            name = client_name or ip
            self.trigger_alert(
                "critical_usage",
                f"CRITICAL: {name} is using {usage_percent:.1f}% of allocated bandwidth!",
                severity="error",
                data={"ip": ip, "usage_percent": usage_percent}
            )
    
    def get_high_usage_statistics(self) -> Dict:
        """Get statistics about high usage tracking"""
        active_high_usage = sum(
            1 for tracker in self.high_usage_tracker.values()
            if tracker["count"] > 0
        )
        
        return {
            "tracked_clients": len(self.high_usage_tracker),
            "active_high_usage": active_high_usage,
            "thresholds": {
                "sustained": self.thresholds.get("sustained_high_usage", 85),
                "critical": self.thresholds.get("critical_usage", 95)
            }
        }
    
    def get_recent_alerts(self, count: int = 20) -> List[Dict]:
        """Get recent alerts"""
        return self.alert_history[-count:]
    
    def clear_alerts(self):
        """Clear alert history"""
        self.alert_history = []
    
    def set_threshold(self, key: str, value):
        """Update alert threshold"""
        self.thresholds[key] = value
    
    def get_thresholds(self) -> Dict:
        """Get current thresholds"""
        return self.thresholds.copy()


alert_manager = AlertManager()


def log_to_file_handler(alert: Dict):
    """Example: Log alerts to file"""
    try:
        with open("equalnet_alerts.log", "a") as f:
            timestamp = alert["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [{alert['severity']}] {alert['message']}\n")
    except Exception as e:
        print(f"Failed to log alert: {e}")


if __name__ == "__main__":
    manager = AlertManager()
    manager.add_handler(log_to_file_handler)
    
    manager.trigger_alert(
        "test",
        "This is a test alert",
        severity="info"
    )
    
    manager.check_bandwidth_limit(95, 100, "192.168.1.100", "Test Device")
    
    print(f"\n📊 Recent alerts: {len(manager.get_recent_alerts())}")
