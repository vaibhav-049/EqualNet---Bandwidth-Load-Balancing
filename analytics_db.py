"""
Database Module for Historical Analytics
Stores bandwidth usage, client history, and generates reports
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class AnalyticsDB:
    def __init__(self, db_path: str = "equalnet.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Bandwidth usage history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bandwidth_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_upload REAL,
                total_download REAL,
                total_clients INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT NOT NULL,
                mac_address TEXT,
                vendor TEXT,
                device_type TEXT,
                priority INTEGER,
                allocated_bandwidth REAL,
                used_bandwidth REAL,
                upload_speed REAL,
                download_speed REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_metadata (
                ip_address TEXT PRIMARY KEY,
                mac_address TEXT,
                vendor TEXT,
                device_type TEXT,
                friendly_name TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_sessions INTEGER DEFAULT 0
            )
        ''')
        
        # Alerts history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                ip_address TEXT,
                message TEXT,
                severity TEXT
            )
        ''')
        
        # Configuration history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                config_key TEXT,
                config_value TEXT,
                changed_by TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_bandwidth(self, upload: float, download: float, clients: int):
        """Log overall bandwidth usage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bandwidth_history 
            (total_upload, total_download, total_clients)
            VALUES (?, ?, ?)
        ''', (upload, download, clients))
        conn.commit()
        conn.close()
    
    def log_client_usage(self, client_data: Dict):
        """Log individual client usage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO client_history
            (ip_address, mac_address, vendor, device_type, priority,
             allocated_bandwidth, used_bandwidth, upload_speed, download_speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_data.get('ip', ''),
            client_data.get('mac', ''),
            client_data.get('vendor', ''),
            client_data.get('device_type', ''),
            client_data.get('priority', 1),
            client_data.get('allocated', 0),
            client_data.get('usage', 0),
            client_data.get('upload', 0),
            client_data.get('download', 0)
        ))
        conn.commit()
        conn.close()
    
    def update_client_metadata(self, ip: str, mac: str, vendor: str,
                               device_type: str, friendly_name: str):
        """Update or insert client metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT ip_address FROM client_metadata WHERE ip_address = ?',
            (ip,)
        )
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute('''
                UPDATE client_metadata
                SET mac_address = ?, vendor = ?, device_type = ?,
                    friendly_name = ?, last_seen = CURRENT_TIMESTAMP,
                    total_sessions = total_sessions + 1
                WHERE ip_address = ?
            ''', (mac, vendor, device_type, friendly_name, ip))
        else:
            cursor.execute('''
                INSERT INTO client_metadata
                (ip_address, mac_address, vendor, device_type, friendly_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip, mac, vendor, device_type, friendly_name))
        
        conn.commit()
        conn.close()
    
    def log_alert(self, alert_type: str, ip: str, message: str,
                  severity: str = "info"):
        """Log an alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alerts (alert_type, ip_address, message, severity)
            VALUES (?, ?, ?, ?)
        ''', (alert_type, ip, message, severity))
        conn.commit()
        conn.close()
    
    def get_bandwidth_history(self, hours: int = 24) -> List[Dict]:
        """Get bandwidth history for last N hours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT * FROM bandwidth_history
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_client_usage_summary(self, ip: str,
                                 hours: int = 24) -> Dict:
        """Get usage summary for a client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT 
                AVG(used_bandwidth) as avg_usage,
                MAX(used_bandwidth) as peak_usage,
                AVG(upload_speed) as avg_upload,
                AVG(download_speed) as avg_download,
                COUNT(*) as data_points
            FROM client_history
            WHERE ip_address = ? AND timestamp >= ?
        ''', (ip, since))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else {}
    
    def get_top_clients(self, limit: int = 10,
                       hours: int = 24) -> List[Dict]:
        """Get top bandwidth consuming clients"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT 
                ip_address,
                AVG(used_bandwidth) as avg_usage,
                SUM(used_bandwidth) as total_usage,
                COUNT(*) as sessions
            FROM client_history
            WHERE timestamp >= ?
            GROUP BY ip_address
            ORDER BY total_usage DESC
            LIMIT ?
        ''', (since, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_hourly_stats(self, hours: int = 24) -> List[Dict]:
        """Get hourly aggregated statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d %H:00', timestamp) as hour,
                AVG(total_upload) as avg_upload,
                AVG(total_download) as avg_download,
                MAX(total_upload) as peak_upload,
                MAX(total_download) as peak_download,
                AVG(total_clients) as avg_clients
            FROM bandwidth_history
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY hour
        ''', (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_daily_report(self, days: int = 7) -> Dict:
        """Generate daily report"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT ip_address) as unique_clients,
                AVG(used_bandwidth) as avg_bandwidth,
                MAX(used_bandwidth) as peak_bandwidth
            FROM client_history
            WHERE timestamp >= ?
        ''', (since,))
        overall = dict(cursor.fetchone())
        
        # Peak hour
        cursor.execute('''
            SELECT 
                strftime('%H:00', timestamp) as hour,
                AVG(total_upload + total_download) as avg_traffic
            FROM bandwidth_history
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY avg_traffic DESC
            LIMIT 1
        ''', (since,))
        peak_row = cursor.fetchone()
        peak_hour = dict(peak_row) if peak_row else {"hour": "N/A", "avg_traffic": 0}
        
        conn.close()
        
        return {
            "period_days": days,
            "unique_clients": overall.get("unique_clients", 0),
            "avg_bandwidth": round(overall.get("avg_bandwidth", 0), 2),
            "peak_bandwidth": round(overall.get("peak_bandwidth", 0), 2),
            "peak_hour": peak_hour.get("hour", "N/A"),
            "peak_traffic": round(peak_hour.get("avg_traffic", 0), 2)
        }
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_clients(self) -> List[Dict]:
        """Get all known clients with metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM client_metadata
            ORDER BY last_seen DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def cleanup_old_data(self, days: int = 30):
        """Remove old data to keep database size manageable"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor.execute(
            'DELETE FROM bandwidth_history WHERE timestamp < ?',
            (cutoff,)
        )
        cursor.execute(
            'DELETE FROM client_history WHERE timestamp < ?',
            (cutoff,)
        )
        cursor.execute(
            'DELETE FROM alerts WHERE timestamp < ?',
            (cutoff,)
        )
        
        conn.commit()
        conn.close()


if __name__ == "__main__":
    db = AnalyticsDB("test_equalnet.db")
    
    db.log_bandwidth(100.5, 250.3, 3)
    db.log_alert("high_usage", "192.168.1.100", "Bandwidth limit exceeded", "warning")
    
    print("✅ Database initialized successfully!")
    print(f"📊 Recent alerts: {len(db.get_recent_alerts())}")
