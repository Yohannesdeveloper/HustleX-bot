import sys
import os

# Create log directory if it doesn't exist
log_dir = "C:\\nssm"
os.makedirs(log_dir, exist_ok=True)

# Open log file
with open(os.path.join(log_dir, "test_output.log"), "w") as f:
    # Write Python version and path
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    
    # Try to import telegram module
    try:
        import telegram
        f.write(f"Telegram module found: {telegram.__version__}\n")
    except ImportError as e:
        f.write(f"Error importing telegram module: {e}\n")
    
    # Try to import python-telegram-bot module
    try:
        import telegram.ext
        f.write(f"Telegram.ext module found\n")
    except ImportError as e:
        f.write(f"Error importing telegram.ext module: {e}\n")

print("Test completed. Check C:\\nssm\\test_output.log for results.")