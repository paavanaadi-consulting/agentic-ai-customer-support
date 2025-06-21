"""
Cleanup script to remove old logs and temporary files.
"""
import os
import shutil

def cleanup_logs(log_dir='logs'):
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
        print(f"Removed log directory: {log_dir}")
    else:
        print(f"Log directory not found: {log_dir}")

def cleanup_temp(temp_dir='tmp'):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Removed temp directory: {temp_dir}")
    else:
        print(f"Temp directory not found: {temp_dir}")

if __name__ == "__main__":
    cleanup_logs()
    cleanup_temp()
