"""
QoS Manager - Quality of Service with Dynamic Priority Adjustment
Automatically detects application types and adjusts priorities
"""
import time
from typing import Dict, List, Tuple
import re


class QoSManager:
    def __init__(self):
        # Application detection patterns (port-based)
        self.app_signatures = {
            # VoIP/Video Conferencing - HIGHEST PRIORITY
            "voip": {
                "ports": [3478, 3479, 5060, 5061, 8801, 16384, 19302],
                "keywords": ["zoom", "teams", "webex", "skype", "meet"],
                "priority": 1,
                "min_bandwidth": 2  # MB/s
            },
            # Gaming - HIGH PRIORITY
            "gaming": {
                "ports": [27015, 27016, 3074, 3478, 27036],
                "keywords": ["steam", "epic", "origin", "battlenet"],
                "priority": 1,
                "min_bandwidth": 1.5
            },
            # Streaming - MEDIUM-HIGH PRIORITY
            "streaming": {
                "ports": [443, 1935, 8080],
                "keywords": ["youtube", "netflix", "twitch", "hotstar"],
                "priority": 2,
                "min_bandwidth": 3
            },
            # File Download - MEDIUM PRIORITY
            "download": {
                "ports": [80, 443, 8080],
                "keywords": ["download", "torrent", "update"],
                "priority": 3,
                "min_bandwidth": 1
            },
            # Browsing - NORMAL PRIORITY
            "browsing": {
                "ports": [80, 443],
                "keywords": ["http", "https"],
                "priority": 4,
                "min_bandwidth": 0.5
            },
            # Background - LOW PRIORITY
            "background": {
                "ports": [],
                "keywords": ["backup", "sync", "update"],
                "priority": 5,
                "min_bandwidth": 0.2
            }
        }
        
        # Client usage history for smart priority adjustment
        self.usage_history = {}
        self.priority_adjustments = {}
        self.last_adjustment_time = {}
        
        # Dynamic adjustment thresholds
        self.HEAVY_USER_THRESHOLD = 50  # MB in 5 minutes
        self.LIGHT_USER_THRESHOLD = 5   # MB in 5 minutes
        self.ADJUSTMENT_INTERVAL = 300  # 5 minutes
        
    def detect_application_type(self, ip: str, 
                                usage_pattern: Dict) -> str:
        """
        Detect application type based on traffic patterns
        """
        # Check bandwidth usage pattern
        upload = usage_pattern.get('upload', 0)
        download = usage_pattern.get('download', 0)
        total = upload + download
        
        # VoIP detection: balanced upload/download
        if upload > 0 and download > 0:
            ratio = upload / download if download > 0 else 0
            if 0.3 < ratio < 3.0 and total < 5:  # Balanced, low bandwidth
                return "voip"
        
        # Streaming detection: high download, low upload
        if download > upload * 5 and download > 2:
            return "streaming"
        
        # Gaming detection: frequent small packets (low total, balanced)
        if 0.5 < total < 2 and 0.5 < ratio < 2.0:
            return "gaming"
        
        # Heavy download: asymmetric, high download
        if download > 10 and download > upload * 10:
            return "download"
        
        # Default to browsing
        return "browsing"
    
    def calculate_dynamic_priority(self, ip: str, 
                                   current_usage: float,
                                   app_type: str = "browsing") -> int:
        """
        Calculate dynamic priority based on usage patterns
        """
        # Get base priority from application type
        base_priority = self.app_signatures[app_type]["priority"]
        
        # Initialize history if new client
        if ip not in self.usage_history:
            self.usage_history[ip] = []
            self.last_adjustment_time[ip] = time.time()
        
        # Add current usage to history
        self.usage_history[ip].append({
            "usage": current_usage,
            "timestamp": time.time()
        })
        
        # Keep only last 5 minutes of history
        current_time = time.time()
        self.usage_history[ip] = [
            h for h in self.usage_history[ip]
            if current_time - h["timestamp"] < 300
        ]
        
        # Calculate total usage in last 5 minutes
        total_usage = sum(h["usage"] for h in self.usage_history[ip])
        
        # Check if adjustment is needed
        if current_time - self.last_adjustment_time[ip] > 60:  # Check every minute
            adjusted_priority = base_priority
            
            # Heavy user penalty (lower priority)
            if total_usage > self.HEAVY_USER_THRESHOLD:
                # Don't penalize critical apps (VoIP, Gaming)
                if app_type not in ["voip", "gaming"]:
                    adjusted_priority = min(5, base_priority + 1)
                    reason = "heavy usage"
            
            # Light user bonus (higher priority)
            elif total_usage < self.LIGHT_USER_THRESHOLD:
                adjusted_priority = max(1, base_priority - 1)
                reason = "light usage"
            else:
                adjusted_priority = base_priority
                reason = "normal usage"
            
            # Store adjustment
            if ip not in self.priority_adjustments or \
               self.priority_adjustments[ip]["priority"] != adjusted_priority:
                self.priority_adjustments[ip] = {
                    "priority": adjusted_priority,
                    "reason": reason,
                    "app_type": app_type,
                    "timestamp": current_time
                }
            
            self.last_adjustment_time[ip] = current_time
            return adjusted_priority
        
        # Return current adjusted priority or base priority
        if ip in self.priority_adjustments:
            return self.priority_adjustments[ip]["priority"]
        return base_priority
    
    def get_qos_rules(self, ip: str, app_type: str) -> Dict:
        """
        Get QoS rules for a client
        """
        if app_type in self.app_signatures:
            app_config = self.app_signatures[app_type]
            return {
                "priority": app_config["priority"],
                "min_bandwidth": app_config["min_bandwidth"],
                "max_latency": 50 if app_type in ["voip", "gaming"] else 200,
                "packet_loss_tolerance": 0.01 if app_type == "voip" else 0.05
            }
        
        # Default rules
        return {
            "priority": 4,
            "min_bandwidth": 0.5,
            "max_latency": 200,
            "packet_loss_tolerance": 0.05
        }
    
    def optimize_priorities(self, clients: List[Dict]) -> Dict[str, int]:
        """
        Optimize priorities for all clients based on usage patterns
        """
        optimized = {}
        
        for client in clients:
            ip = client['ip']
            usage = client.get('usage', 0)
            
            # Detect application type
            usage_pattern = {
                'upload': client.get('upload', 0),
                'download': client.get('download', 0)
            }
            app_type = self.detect_application_type(ip, usage_pattern)
            
            # Calculate dynamic priority
            priority = self.calculate_dynamic_priority(ip, usage, app_type)
            
            optimized[ip] = {
                "priority": priority,
                "app_type": app_type,
                "qos_rules": self.get_qos_rules(ip, app_type)
            }
        
        return optimized
    
    def get_priority_explanation(self, ip: str) -> str:
        """
        Get human-readable explanation for priority adjustment
        """
        if ip in self.priority_adjustments:
            adj = self.priority_adjustments[ip]
            app_name = adj['app_type'].title()
            reason = adj['reason']
            priority = adj['priority']
            
            return (f"Priority {priority} - {app_name} traffic detected, "
                   f"adjusted for {reason}")
        return "Priority based on default rules"
    
    def get_statistics(self) -> Dict:
        """
        Get QoS statistics
        """
        stats = {
            "total_clients_monitored": len(self.usage_history),
            "active_adjustments": len(self.priority_adjustments),
            "app_type_distribution": {}
        }
        
        # Count application types
        for adj in self.priority_adjustments.values():
            app_type = adj['app_type']
            stats['app_type_distribution'][app_type] = \
                stats['app_type_distribution'].get(app_type, 0) + 1
        
        return stats


if __name__ == "__main__":
    # Test QoS Manager
    qos = QoSManager()
    
    # Simulate clients
    test_clients = [
        {"ip": "192.168.1.10", "usage": 45, "upload": 2, "download": 2},  # VoIP
        {"ip": "192.168.1.11", "usage": 80, "upload": 1, "download": 15}, # Streaming
        {"ip": "192.168.1.12", "usage": 5, "upload": 0.5, "download": 0.8}, # Gaming
    ]
    
    optimized = qos.optimize_priorities(test_clients)
    for ip, info in optimized.items():
        print(f"{ip}: Priority {info['priority']} ({info['app_type']})")
    
    print("\nStatistics:", qos.get_statistics())
