import os
import sys
import time
import logging
import subprocess
import signal
import threading
from datetime import datetime, timedelta

# Set up logging
log_file = 'C:\\nssm\\hustlex_service.log'
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)  # Also log to console
    ]
)

class BotService:
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.max_restarts = 50  # Increased for better resilience
        self.restart_delay = 5  # seconds
        self.max_restart_delay = 300  # 5 minutes
        self.last_restart = datetime.now()
        self.shutdown_event = threading.Event()
        self.consecutive_failures = 0
        self.last_successful_start = datetime.now()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown_event.set()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logging.warning("Process didn't terminate gracefully, forcing kill")
                self.process.kill()
    
    def start_bot_process(self):
        """Start the bot process"""
        try:
            # Change to the project directory
            project_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(project_dir)
            
            # Path to the virtual environment Python
            venv_python = os.path.join(project_dir, '.venv', 'Scripts', 'python.exe')
            
            # If venv doesn't exist, try system Python
            if not os.path.exists(venv_python):
                logging.warning(f"Virtual environment not found: {venv_python}")
                # Try system Python
                import sys
                venv_python = sys.executable
                logging.info(f"Using system Python: {venv_python}")
            
            if not os.path.exists(venv_python):
                logging.error(f"Python executable not found: {venv_python}")
                return False
                
            logging.info(f"Starting bot process with Python: {venv_python}")
            
            # Start the bot process
            bot_main_path = os.path.join(project_dir, 'bot', 'main.py')
            self.process = subprocess.Popen(
                [venv_python, bot_main_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=project_dir
            )
            
            logging.info(f"Bot process started with PID: {self.process.pid}")
            self.consecutive_failures = 0
            self.last_successful_start = datetime.now()
            return True
            
        except Exception as e:
            logging.error(f"Failed to start bot process: {e}")
            self.consecutive_failures += 1
            return False
    
    def restart_bot_process(self):
        """Restart the bot process with exponential backoff"""
        current_time = datetime.now()
        time_since_last_restart = (current_time - self.last_restart).total_seconds()
        
        # Calculate delay with exponential backoff
        delay = min(self.restart_delay * (2 ** min(self.restart_count, 8)), self.max_restart_delay)
        
        if time_since_last_restart < delay:
            sleep_time = delay - time_since_last_restart
            logging.info(f"Waiting {sleep_time:.1f} seconds before restart (exponential backoff)")
            time.sleep(sleep_time)
        
        self.restart_count += 1
        self.last_restart = datetime.now()
        
        if self.restart_count > self.max_restarts:
            logging.error(f"Maximum restart attempts ({self.max_restarts}) exceeded. Service stopping.")
            return False
            
        logging.info(f"Restarting bot process (attempt {self.restart_count}/{self.max_restarts})")
        
        # Clean up old process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logging.warning(f"Error terminating old process: {e}")
        
        return self.start_bot_process()
    
    def health_check(self):
        """Perform health checks on the bot process"""
        try:
            if self.process is None:
                return False
            
            # Check if process is still running
            if self.process.poll() is not None:
                return False
            
            # Check if process has been running for a reasonable time
            time_since_start = (datetime.now() - self.last_successful_start).total_seconds()
            if time_since_start < 30:  # Less than 30 seconds, might be starting up
                return True
            
            # Additional health checks could be added here
            # For example, checking if the bot responds to a test command
            return True
            
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False
    
    def monitor_process(self):
        """Monitor the bot process and restart if needed"""
        while not self.shutdown_event.is_set():
            try:
                if self.process is None:
                    if not self.start_bot_process():
                        logging.error("Failed to start initial bot process")
                        break
                
                # Check if process is still running
                if self.process.poll() is not None:
                    # Process has exited
                    out, err = self.process.communicate()
                    exit_code = self.process.returncode
                    
                    logging.error(f"Bot process exited with code {exit_code}")
                    if out:
                        logging.error(f"STDOUT: {out}")
                    if err:
                        logging.error(f"STDERR: {err}")
                    
                    # Reset restart count if it's been a while since last restart
                    if (datetime.now() - self.last_restart).total_seconds() > 3600:  # 1 hour
                        self.restart_count = 0
                        logging.info("Resetting restart count after 1 hour of stable operation")
                    
                    # Attempt to restart
                    if not self.restart_bot_process():
                        break
                else:
                    # Process is running, perform health check
                    if not self.health_check():
                        logging.warning("Health check failed, restarting bot process")
                        if not self.restart_bot_process():
                            break
                
                # Sleep to avoid high CPU usage
                time.sleep(5)
                
            except Exception as e:
                logging.exception(f"Error in monitor loop: {e}")
                time.sleep(10)
    
    def run(self):
        """Main service loop"""
        try:
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self.signal_handler)
            signal.signal(signal.SIGINT, self.signal_handler)
            
            logging.info("Starting HustleX Bot service")
            logging.info(f"Service PID: {os.getpid()}")
            
            # Start monitoring
            self.monitor_process()
            
        except Exception as e:
            logging.exception(f"Service error: {e}")
            return 1
        finally:
            logging.info("HustleX Bot service shutting down")
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=10)
                except:
                    self.process.kill()
        
        return 0

def main():
    service = BotService()
    return service.run()

if __name__ == "__main__":
    sys.exit(main())