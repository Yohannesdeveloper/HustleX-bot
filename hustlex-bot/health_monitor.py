#!/usr/bin/env python3
"""
Health Monitor for HustleX Bot
Monitors bot health and sends alerts if issues are detected
"""

import os
import sys
import time
import logging
import subprocess
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
log_file = 'C:\\nssm\\hustlex_health.log'
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class HealthMonitor:
    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = 'C:\\nssm'
        self.service_log = os.path.join(self.log_dir, 'hustlex_service.log')
        self.bot_log = os.path.join(self.log_dir, 'hustlex_bot_output.log')
        self.error_log = os.path.join(self.log_dir, 'hustlex_bot_error.log')
        self.last_check = datetime.now()
        self.alert_threshold = 300  # 5 minutes
        self.restart_threshold = 600  # 10 minutes
        
    def check_service_status(self):
        """Check if the Windows service is running"""
        try:
            result = subprocess.run(
                ['sc', 'query', 'HustleXBot'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                if 'RUNNING' in result.stdout:
                    logging.info("HustleXBot service is running")
                    return True
                else:
                    logging.warning("HustleXBot service is not running")
                    return False
            else:
                logging.error(f"Failed to check service status: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error checking service status: {e}")
            return False
    
    def check_bot_process(self):
        """Check if bot process is running"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Look for bot.main in the command line
                bot_processes = []
                for line in result.stdout.split('\n'):
                    if 'bot.main' in line.lower():
                        bot_processes.append(line)
                
                if bot_processes:
                    logging.info(f"Found {len(bot_processes)} bot process(es) running")
                    return True
                else:
                    logging.warning("No bot processes found")
                    return False
            else:
                logging.error(f"Failed to check bot processes: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error checking bot processes: {e}")
            return False
    
    def check_log_files(self):
        """Check log files for errors and activity"""
        issues = []
        
        # Check service log
        if os.path.exists(self.service_log):
            try:
                with open(self.service_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:]  # Last 50 lines
                    
                    for line in recent_lines:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            # Check if error is recent (within last hour)
                            try:
                                timestamp_str = line.split(' - ')[0]
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                if datetime.now() - timestamp < timedelta(hours=1):
                                    issues.append(f"Recent service error: {line.strip()}")
                            except:
                                issues.append(f"Service log error: {line.strip()}")
            except Exception as e:
                logging.error(f"Error reading service log: {e}")
        
        # Check error log
        if os.path.exists(self.error_log):
            try:
                with open(self.error_log, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        # Check if error log was modified recently
                        mod_time = datetime.fromtimestamp(os.path.getmtime(self.error_log))
                        if datetime.now() - mod_time < timedelta(hours=1):
                            issues.append(f"Recent errors in error log (modified {mod_time})")
            except Exception as e:
                logging.error(f"Error reading error log: {e}")
        
        return issues
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_dir)
            free_gb = free // (1024**3)
            
            if free_gb < 1:  # Less than 1GB free
                return f"Low disk space: {free_gb}GB free"
            else:
                logging.info(f"Disk space OK: {free_gb}GB free")
                return None
                
        except Exception as e:
            logging.error(f"Error checking disk space: {e}")
            return "Unable to check disk space"
    
    def check_network_connectivity(self):
        """Check network connectivity to Telegram API"""
        try:
            # Try to reach Telegram API
            response = requests.get('https://api.telegram.org', timeout=10)
            if response.status_code == 200:
                logging.info("Network connectivity OK")
                return True
            else:
                logging.warning(f"Telegram API returned status {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Network connectivity issue: {e}")
            return False
    
    def restart_service(self):
        """Attempt to restart the service"""
        try:
            logging.info("Attempting to restart HustleXBot service...")
            
            # Stop service
            subprocess.run(['sc', 'stop', 'HustleXBot'], timeout=30)
            time.sleep(5)
            
            # Start service
            result = subprocess.run(['sc', 'start', 'HustleXBot'], timeout=30)
            
            if result.returncode == 0:
                logging.info("Service restarted successfully")
                return True
            else:
                logging.error("Failed to restart service")
                return False
                
        except Exception as e:
            logging.error(f"Error restarting service: {e}")
            return False
    
    def send_alert(self, message):
        """Send alert notification (placeholder for future implementation)"""
        logging.critical(f"ALERT: {message}")
        # TODO: Implement actual alert mechanism (email, SMS, webhook, etc.)
        # For now, just log the alert
    
    def run_health_check(self):
        """Run comprehensive health check"""
        logging.info("Starting health check...")
        
        issues = []
        
        # Check service status
        if not self.check_service_status():
            issues.append("HustleXBot service is not running")
        
        # Check bot process
        if not self.check_bot_process():
            issues.append("No bot processes found")
        
        # Check log files
        log_issues = self.check_log_files()
        issues.extend(log_issues)
        
        # Check disk space
        disk_issue = self.check_disk_space()
        if disk_issue:
            issues.append(disk_issue)
        
        # Check network connectivity
        if not self.check_network_connectivity():
            issues.append("Network connectivity issues detected")
        
        # Handle issues
        if issues:
            alert_message = f"Health check failed. Issues: {'; '.join(issues)}"
            self.send_alert(alert_message)
            
            # If critical issues, try to restart service
            if len(issues) > 2 or "service is not running" in str(issues):
                logging.warning("Critical issues detected, attempting service restart...")
                self.restart_service()
        else:
            logging.info("Health check passed - all systems OK")
        
        self.last_check = datetime.now()
        return len(issues) == 0
    
    def run_monitor(self):
        """Run continuous monitoring"""
        logging.info("Starting continuous health monitoring...")
        
        while True:
            try:
                self.run_health_check()
                
                # Sleep for 5 minutes before next check
                time.sleep(300)
                
            except KeyboardInterrupt:
                logging.info("Health monitor stopped by user")
                break
            except Exception as e:
                logging.exception(f"Error in health monitor: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    monitor = HealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run single health check
        success = monitor.run_health_check()
        sys.exit(0 if success else 1)
    else:
        # Run continuous monitoring
        monitor.run_monitor()

if __name__ == "__main__":
    main()
