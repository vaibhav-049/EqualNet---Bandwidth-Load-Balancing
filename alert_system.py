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
            "unusual_traffic": True
        }
        self.alert_history = []
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
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        # Console output with color
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }.get(severity, "📢")
        
        print(f"{emoji} [{severity.upper()}] {message}")
        
        # Call custom handlers
        for handler in self.alert_handlers:
            try:
                threading.Thread(
                    target=handler,
                    args=(alert,),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"❌ Alert handler error: {e}")
        
        # Send email for important alerts
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
        
        # Sort by priority (lower number = higher priority)
        sorted_clients = sorted(clients, key=lambda x: x.get("priority", 999))
        
        for i in range(len(sorted_clients) - 1):
            high_pri = sorted_clients[i]
            low_pri = sorted_clients[i + 1]
            
            # Only alert if priority difference is significant (>2 levels)
            priority_diff = low_pri.get("priority", 5) - high_pri.get("priority", 1)
            if priority_diff < 2:
                continue
            
            high_usage = high_pri.get("usage", 0)
            low_usage = low_pri.get("usage", 0)
            
            # Only alert if BOTH are using significant bandwidth
            # AND low priority is using much more (2x not 1.5x)
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
        
        # Alert if usage is 3x the average
        if current_usage > avg_usage * 3:
            self.trigger_alert(
                "unusual_traffic",
                f"Unusual traffic detected from {ip}: {current_usage:.2f} MB/s (avg: {avg_usage:.2f} MB/s)",
                severity="warning",
                data={"ip": ip, "current": current_usage, "average": avg_usage}
            )
    
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


# Global alert manager instance
alert_manager = AlertManager()


# Example custom handler
def log_to_file_handler(alert: Dict):
    """Example: Log alerts to file"""
    try:
        with open("equalnet_alerts.log", "a") as f:
            timestamp = alert["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [{alert['severity']}] {alert['message']}\n")
    except Exception as e:
        print(f"Failed to log alert: {e}")


if __name__ == "__main__":
    # Test alerts
    manager = AlertManager()
    manager.add_handler(log_to_file_handler)
    
    manager.trigger_alert(
        "test",
        "This is a test alert",
        severity="info"
    )
    
    manager.check_bandwidth_limit(95, 100, "192.168.1.100", "Test Device")
    
    print(f"\n📊 Recent alerts: {len(manager.get_recent_alerts())}")
